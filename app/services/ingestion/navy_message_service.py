from __future__ import annotations

import hashlib
import re

import httpx
from bs4 import BeautifulSoup

from app.schemas.ingestion import MessageRecord
from app.schemas.message_watch import MessageWatchRefreshResponse
from app.services.ingestion.message_record_store import MessageRecordStore

_NAVY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36"
}

OFFICIAL_NAVADMIN_YEAR_URL = "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN-2026/"
OFFICIAL_ALNAV_YEAR_URL = "https://www.mynavyhr.navy.mil/References/Messages/ALNAV-2026/"

_ROW_PATTERN = re.compile(
    r"^(?P<number>\d{3}/\d{2})\s+(?P<title>.+?)\s+(?P<date>\d{2}/\d{2}/\d{4})$"
)


class NavyMessageService:
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def refresh_navadmins(self, store: MessageRecordStore) -> MessageWatchRefreshResponse:
        return self._refresh(store=store, url=OFFICIAL_NAVADMIN_YEAR_URL, source_family="NAVADMIN")

    def refresh_alnavs(self, store: MessageRecordStore) -> MessageWatchRefreshResponse:
        return self._refresh(store=store, url=OFFICIAL_ALNAV_YEAR_URL, source_family="ALNAV")

    def parse_year_page(self, html_text: str, *, source_family: str, source_url: str) -> list[MessageRecord]:
        soup = BeautifulSoup(html_text, "html.parser")
        lines = [
            " ".join(line.split())
            for line in soup.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]
        records: list[MessageRecord] = []
        for line in lines:
            match = _ROW_PATTERN.match(line)
            if match is None:
                continue
            message_number = match.group("number")
            title = match.group("title").strip()
            canonical_url = _build_message_url(source_family=source_family, message_number=message_number)
            source_hash = hashlib.sha256(f"{message_number}\n{title}".encode()).hexdigest()
            records.append(
                MessageRecord(
                    source_id=f"{source_family.lower()}-{message_number.replace('/', '-').lower()}",
                    title=title,
                    canonical_url=canonical_url,
                    message_number=message_number,
                    fiscal_year=2000 + int(message_number.split("/")[-1]),
                    summary=None,
                    tags=_tags(title),
                    source_family=source_family,
                    status="official_message",
                    source_hash=source_hash,
                )
            )
        return records

    def _refresh(self, *, store: MessageRecordStore, url: str, source_family: str) -> MessageWatchRefreshResponse:
        warnings: list[str] = []
        try:
            html_text = self._fetch_html(url)
            records = self.parse_year_page(html_text, source_family=source_family, source_url=url)
            return MessageWatchRefreshResponse(records=store.save_many(records), warnings=warnings)
        except httpx.HTTPStatusError as exc:
            warnings.append(
                f"{source_family} refresh hit HTTP {exc.response.status_code} from the official MyNavyHR source. "
                "Serving cached data if present."
            )
        except httpx.HTTPError as exc:
            warnings.append(f"{source_family} refresh failed against the official MyNavyHR source: {exc}")
        return MessageWatchRefreshResponse(records=store.list(limit=25), warnings=warnings)

    def _fetch_html(self, url: str) -> str:
        with httpx.Client(timeout=self.timeout_seconds, headers=_NAVY_HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        return response.text


def _build_message_url(*, source_family: str, message_number: str) -> str:
    year = 2000 + int(message_number.split("/")[-1])
    compact = source_family[:3].upper() if source_family == "ALNAV" else "NAV"
    file_number = f"{compact}{year}{message_number.split('/')[0]}"
    folder = "ALNAV" if source_family == "ALNAV" else "NAVADMIN"
    return f"https://www.mynavyhr.navy.mil/Portals/55/Messages/{folder}/{compact}{year}/{file_number}.pdf"


def _tags(title: str) -> list[str]:
    haystack = title.lower()
    tag_map = {
        "Reserve": ("reserve", "tar", "retention", "continuation"),
        "Promotion": ("promotion", "selection", "board"),
        "PME": ("education", "seminar", "war college", "training"),
        "Uniform": ("uniform", "grooming"),
        "Travel": ("travel",),
        "Readiness": ("readiness", "family accountability", "health of the force"),
        "Policy": ("policy", "guidance", "implementing"),
    }
    tags = [tag for tag, keywords in tag_map.items() if any(keyword in haystack for keyword in keywords)]
    return tags or ["NavyMessage"]
