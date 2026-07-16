from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from typing import Final
from urllib.parse import SplitResult, urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.schemas.source_library import SourceFetchApproval, SourceFetchPreview, SourceFetchRequest

_ALLOWED_MEDIA_TYPES: Final = frozenset({"text/html", "application/pdf"})
_CLASSIFICATION_PATTERN: Final = re.compile(
    r"\b(?:CUI|CONTROLLED\s+UNCLASSIFIED(?:\s+INFORMATION)?|FOUO|TOP\s+SECRET|SECRET|CONFIDENTIAL|CLASSIFIED|NON[-\s]?UNCLASSIFIED)\b",
    re.IGNORECASE,
)
_LOCAL_HOSTS: Final = frozenset({"localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback"})


class SourceFetchError(ValueError):
    """A source URL, approval, response, or extracted body was not acceptable."""


@dataclass(frozen=True)
class FetchedPublicSource:
    raw_bytes: bytes
    normalized_text: str
    media_type: str
    title: str
    content_hash: str
    byte_size: int
    canonical_url: str


class PublicSourceFetcher:
    """Fetch exactly one user-approved public HTML page or direct PDF."""

    def __init__(
        self,
        client_factory: Callable[[], httpx.Client] | None = None,
        max_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive.")
        self._client_factory = client_factory or (lambda: httpx.Client(follow_redirects=False, timeout=20.0))
        self._max_bytes = max_bytes

    def build_preview(self, user_key: str, request: SourceFetchRequest) -> SourceFetchPreview:
        """Validate a URL without making a network request and bind approval to it."""
        if not user_key.strip():
            raise SourceFetchError("A user key is required for source-fetch approval.")
        canonical_url, host = _validate_public_url(request.url)
        digest = _approval_digest(user_key, request, canonical_url)
        return SourceFetchPreview(
            url=request.url,
            host=host,
            approval_digest=digest,
            finding_categories=["external_network_request", "public_source_content"],
            warnings=[
                "The app will make one request to this exact public URL.",
                "Redirects, private hosts, unsupported media, and non-UNCLASSIFIED content are rejected.",
            ],
        )

    def fetch_approved(
        self,
        user_key: str,
        request: SourceFetchRequest,
        approval: SourceFetchApproval,
        preview: SourceFetchPreview,
    ) -> FetchedPublicSource:
        """Perform the one approved request, validate it, and extract local text."""
        canonical_url, _ = _validate_public_url(request.url)
        expected_digest = _approval_digest(user_key, request, canonical_url)
        if preview.approval_digest != expected_digest or approval.approval_digest != expected_digest:
            raise SourceFetchError("The approval does not match this current source-fetch preview.")
        if preview.url != request.url:
            raise SourceFetchError("The preview URL does not match the requested URL.")
        if not approval.acknowledged:
            raise SourceFetchError("Source fetch approval requires acknowledgement.")
        missing_categories = set(preview.finding_categories).difference(approval.acknowledged_finding_categories)
        if missing_categories:
            raise SourceFetchError("The approval does not acknowledge all preview finding categories.")

        try:
            with self._client_factory() as client, client.stream(
                "GET", canonical_url, follow_redirects=False
            ) as response:
                if 300 <= response.status_code < 400:
                    raise SourceFetchError("Redirect responses are not allowed for approved source URLs.")
                response.raise_for_status()
                media_type = _media_type(response.headers.get("content-type"), canonical_url)
                raw_bytes = _read_limited(response, self._max_bytes)
        except SourceFetchError:
            raise
        except httpx.HTTPError as exc:
            raise SourceFetchError("The approved public URL could not be retrieved.") from exc

        normalized_text, extracted_title = _extract(media_type, raw_bytes)
        _reject_non_unclassified(normalized_text)
        return FetchedPublicSource(
            raw_bytes=raw_bytes,
            normalized_text=normalized_text,
            media_type=media_type,
            title=request.title or extracted_title or canonical_url,
            content_hash=hashlib.sha256(raw_bytes).hexdigest(),
            byte_size=len(raw_bytes),
            canonical_url=canonical_url,
        )


def _validate_public_url(value: str) -> tuple[str, str]:
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise SourceFetchError("The source URL is invalid.") from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SourceFetchError("Only public HTTP(S) source URLs are allowed.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise SourceFetchError("The source URL must contain a public host and no credentials.")
    host = parsed.hostname.lower().rstrip(".")
    if _is_private_or_loopback_host(host):
        raise SourceFetchError("Private, loopback, and local source hosts are not allowed.")
    if parsed.fragment:
        parsed = parsed._replace(fragment="")
    canonical = urlunsplit(
        SplitResult(parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.query, parsed.fragment)
    )
    return canonical, host


def _is_private_or_loopback_host(host: str) -> bool:
    if host in _LOCAL_HOSTS or host.endswith((".localhost", ".local", ".internal", ".lan", ".home")):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return not address.is_global


def _approval_digest(user_key: str, request: SourceFetchRequest, canonical_url: str) -> str:
    payload = json.dumps(
        {"user_key": user_key, "url": canonical_url, "title": request.title, "publisher": request.publisher},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _media_type(content_type: str | None, canonical_url: str) -> str:
    normalized = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized in _ALLOWED_MEDIA_TYPES:
        return normalized
    if not normalized and canonical_url.lower().endswith(".pdf"):
        return "application/pdf"
    raise SourceFetchError("Only HTML pages and direct PDF sources are supported.")


def _read_limited(response: httpx.Response, max_bytes: int) -> bytes:
    content_length = response.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > max_bytes:
                raise SourceFetchError("The source response exceeds the configured size limit.")
        except ValueError as exc:
            raise SourceFetchError("The source response has an invalid Content-Length.") from exc
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > max_bytes:
            raise SourceFetchError("The source response exceeds the configured size limit.")
        chunks.append(chunk)
    return b"".join(chunks)


def _extract(media_type: str, raw_bytes: bytes) -> tuple[str, str]:
    if media_type == "text/html":
        soup = BeautifulSoup(raw_bytes, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag is not None else ""
        return soup.get_text(" ", strip=True), title
    try:
        reader = PdfReader(BytesIO(raw_bytes))
        return " ".join(page.extract_text() or "" for page in reader.pages).strip(), ""
    except Exception as exc:
        raise SourceFetchError("The PDF source could not be parsed.") from exc


def _reject_non_unclassified(text: str) -> None:
    if _CLASSIFICATION_PATTERN.search(text):
        raise SourceFetchError("The source contains a CUI or non-UNCLASSIFIED classification label.")
