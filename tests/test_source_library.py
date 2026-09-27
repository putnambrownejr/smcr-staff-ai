from io import BytesIO
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings, configured_storage_dirs, default_source_library_dir
from app.schemas.source_library import SavedSource, SourceFetchApproval, SourceFetchPreview, SourceFetchRequest
from app.schemas.source_state import VerifiedSourceStatus
from app.services.rag.chunking import TextChunk
from app.services.source_library.fetcher import FetchedPublicSource, PublicSourceFetcher, SourceFetchError
from app.services.source_library.service import (
    SourceLibraryRecheckRequest,
    SourceLibraryReviewRequest,
    SourceLibraryService,
)
from app.services.source_library.store import SourceLibraryStore


def test_source_fetch_approval_requires_acknowledgement() -> None:
    with pytest.raises(ValidationError):
        SourceFetchApproval(approval_digest="a" * 64, acknowledged=False)


def test_source_library_storage_is_under_local_context() -> None:
    assert default_source_library_dir().name == "source_library"
    assert default_source_library_dir().parent.name == "local_context"


def test_source_library_storage_dir_is_configured() -> None:
    settings = Settings()

    assert settings.source_library_storage_dir == str(default_source_library_dir())
    assert default_source_library_dir() in configured_storage_dirs(settings)


def test_store_isolates_users_and_removes_content(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source = SavedSource(
        source_id="source-alpha",
        user_key_digest="0" * 64,
        original_url="https://example.test/alpha",
        canonical_url="https://example.test/alpha",
        title="Alpha source",
        media_type="text/html",
        content_hash="a" * 64,
        byte_size=12,
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
    )
    chunks = [TextChunk(chunk_index=0, text="Alpha public planning text")]

    saved = store.save("user-a", source, b"<p>alpha</p>", "alpha", chunks)

    assert saved.user_key_digest == store.user_key_digest("user-a")
    assert store.list("user-b") == []
    hits = store.search("user-a", "alpha", None, 5)
    assert [hit.chunk.text for hit in hits] == ["Alpha public planning text"]
    assert store.remove("user-a", saved.source_id) is True
    assert store.get("user-a", saved.source_id) is None
    assert store.search("user-a", "alpha", None, 5) == []
    assert not (tmp_path / store.user_key_digest("user-a")).exists()


def test_review_and_recheck_update_metadata_without_writing_source_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SourceLibraryStore(tmp_path)
    source = SavedSource(
        source_id="source-alpha",
        user_key_digest=store.user_key_digest("user-a"),
        original_url="https://example.test/alpha",
        canonical_url="https://example.test/alpha",
        title="Alpha source",
        media_type="text/html",
        content_hash="a" * 64,
        byte_size=12,
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
    )
    saved = store.save("user-a", source, b"<p>retained</p>", "retained text", [TextChunk(chunk_index=0, text="retained text")])
    user_dir = tmp_path / store.user_key_digest("user-a")
    content_paths = [user_dir / saved.raw_content_path, user_dir / saved.normalized_text_path, user_dir / saved.chunks_path]
    content_before = [path.read_bytes() for path in content_paths]

    class FakeFetcher:
        def build_preview(self, user_key: str, request: SourceFetchRequest) -> object:
            del user_key, request
            return object()

        def fetch_approved(self, user_key: str, request: SourceFetchRequest, approval: object, preview: object) -> FetchedPublicSource:
            del user_key, request, approval, preview
            return FetchedPublicSource(
                raw_bytes=b"candidate", normalized_text="candidate", media_type="text/html", title="Alpha source",
                content_hash="b" * 64, byte_size=9, canonical_url="https://example.test/alpha",
            )

    def reject_raw_write(_path: Path, _data: bytes) -> int:
        pytest.fail("metadata-only operation attempted to write source bytes")

    monkeypatch.setattr(Path, "write_bytes", reject_raw_write)
    service = SourceLibraryService(store, FakeFetcher())  # type: ignore[arg-type]
    reviewed = service.review(
        saved.source_id,
        SourceLibraryReviewRequest(user_key="user-a", status=VerifiedSourceStatus.current, notes="Reviewed"),
    )
    assert reviewed is not None and reviewed.review_notes == "Reviewed"
    rechecked = service.recheck(
        saved.source_id,
        SourceLibraryRecheckRequest(
            user_key="user-a",
            preview=SourceFetchPreview(
                url="https://example.test/alpha", host="example.test", approval_digest="c" * 64
            ),
            approval=SourceFetchApproval(approval_digest="c" * 64, acknowledged=True),
        ),
    )

    assert rechecked is not None and rechecked.content_changed is True
    persisted = store.get("user-a", saved.source_id)
    assert persisted is not None
    assert persisted.trust_status == VerifiedSourceStatus.watch
    assert [path.read_bytes() for path in content_paths] == content_before


def _fetcher(handler: httpx.MockTransport) -> PublicSourceFetcher:
    return PublicSourceFetcher(lambda: httpx.Client(transport=handler, follow_redirects=False), max_bytes=1_024)


def _approved(preview: object) -> SourceFetchApproval:
    assert hasattr(preview, "approval_digest")
    assert hasattr(preview, "finding_categories")
    return SourceFetchApproval(
        approval_digest=preview.approval_digest,
        acknowledged=True,
        acknowledged_finding_categories=preview.finding_categories,
    )


def test_fetcher_requires_matching_preview_before_one_html_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><title>Plan</title><body>Public text</body></html>",
            request=request,
        )

    fetcher = _fetcher(httpx.MockTransport(handler))
    source_request = SourceFetchRequest(url="https://example.test/plan")
    preview = fetcher.build_preview("user-a", source_request)
    result = fetcher.fetch_approved("user-a", source_request, _approved(preview), preview)

    assert result.normalized_text == "Plan Public text"
    assert result.title == "Plan"
    assert result.content_hash
    assert len(requests) == 1


@pytest.mark.parametrize(
    "url",
    ["file:///tmp/plan.html", "http://localhost/plan", "http://127.0.0.1/plan", "http://10.0.0.4/plan"],
)
def test_fetcher_rejects_non_public_url_before_network_request(url: str) -> None:
    fetcher = _fetcher(httpx.MockTransport(lambda request: pytest.fail(f"unexpected request: {request.url}")))

    with pytest.raises(SourceFetchError):
        fetcher.build_preview("user-a", SourceFetchRequest(url=url))


def test_fetcher_rejects_redirect_type_size_and_classification() -> None:
    cases = [
        httpx.Response(302, headers={"location": "https://example.test/next"}),
        httpx.Response(200, headers={"content-type": "text/plain"}, content=b"plain"),
        httpx.Response(200, headers={"content-type": "text/html", "content-length": "1025"}, content=b"x"),
        httpx.Response(200, headers={"content-type": "text/html"}, content=b"<p>CUI</p>"),
    ]
    for response in cases:
        def handler(request: httpx.Request, response: httpx.Response = response) -> httpx.Response:
            return httpx.Response(
                response.status_code, headers=response.headers, content=response.content, request=request
            )

        fetcher = _fetcher(httpx.MockTransport(handler))
        source_request = SourceFetchRequest(url="https://example.test/plan")
        preview = fetcher.build_preview("user-a", source_request)
        with pytest.raises(SourceFetchError):
            fetcher.fetch_approved("user-a", source_request, _approved(preview), preview)


def test_fetcher_rejects_stale_approval_and_extracts_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    fetcher = _fetcher(httpx.MockTransport(lambda request: httpx.Response(200, request=request)))
    old_request = SourceFetchRequest(url="https://example.test/old")
    stale_preview = fetcher.build_preview("user-a", old_request)
    current_request = SourceFetchRequest(url="https://example.test/current")
    current_preview = fetcher.build_preview("user-a", current_request)
    with pytest.raises(SourceFetchError):
        fetcher.fetch_approved("user-a", current_request, _approved(stale_preview), current_preview)

    class FakePage:
        def extract_text(self) -> str:
            return "PDF public text"

    class FakeReader:
        pages = [FakePage()]

        def __init__(self, stream: BytesIO) -> None:
            del stream

    monkeypatch.setattr("app.services.source_library.fetcher.PdfReader", FakeReader)
    pdf_fetcher = _fetcher(
        httpx.MockTransport(
            lambda request: httpx.Response(
                200, headers={"content-type": "application/pdf"}, content=b"%PDF", request=request
            )
        )
    )
    pdf_request = SourceFetchRequest(url="https://example.test/plan.pdf")
    pdf_preview = pdf_fetcher.build_preview("user-a", pdf_request)
    result = pdf_fetcher.fetch_approved("user-a", pdf_request, _approved(pdf_preview), pdf_preview)

    assert result.media_type == "application/pdf"
    assert result.normalized_text == "PDF public text"
