"""ALMAR (All Marine) message feed pulled from the official marines.mil RSS.

ALMARs are the Commandant's all-hands messages (holiday and anniversary
messages, Sergeants Major slates, force-wide announcements). They ride the
same DNN RSS endpoint as MARADMINs, just a different category, so unlike
NAVADMIN/ALNAV (which have no public RSS or API and sit behind a WAF on
MyNavyHR) this feed can actually be pulled.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol

import httpx

from app.schemas.ingestion import MessageRecord
from app.schemas.message_watch import MessageWatchRefreshResponse
from app.services.ingestion.maradmin_scraper import tag_message
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.rss_client import FeedItem, RssClient

OFFICIAL_ALMAR_RSS_URL = (
    "https://www.marines.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=6&Site=481&category=14335&max=10"
)
ALMAR_PORTAL_URL = "https://www.marines.mil/News/Messages/ALMARS/"

# The message number lives in the summary header ("R 032026Z SEP 26ALMAR 021/26MSGID/..."),
# and occasionally in the title, so search both without relying on word boundaries.
_NUMBER_PATTERN = re.compile(r"ALMAR\s*(?P<number>\d{3}/\d{2})", re.IGNORECASE)


class RssClientLike(Protocol):
    def fetch_sync(self, url: str) -> list[FeedItem]: ...


class AlmarFeedService:
    def __init__(
        self,
        rss_client: RssClientLike | None = None,
        feed_url: str = OFFICIAL_ALMAR_RSS_URL,
    ) -> None:
        self.rss_client = rss_client or RssClient()
        self.feed_url = feed_url

    def refresh(self, store: MessageRecordStore) -> MessageWatchRefreshResponse:
        try:
            items = self.rss_client.fetch_sync(self.feed_url)
        except httpx.HTTPStatusError as exc:
            return MessageWatchRefreshResponse(
                records=store.list(limit=25),
                warnings=[
                    f"ALMAR refresh hit HTTP {exc.response.status_code} from the official marines.mil RSS source. "
                    "Serving cached data if present."
                ],
            )
        except httpx.HTTPError as exc:
            return MessageWatchRefreshResponse(
                records=store.list(limit=25),
                warnings=[f"ALMAR refresh failed against the official marines.mil RSS source: {exc}"],
            )
        records = [almar_record_from_feed_item(item) for item in items]
        return MessageWatchRefreshResponse(records=store.save_many(records))


def parse_almar_number(text: str) -> tuple[str | None, int | None]:
    match = _NUMBER_PATTERN.search(text)
    if match is None:
        return None, None
    number = match.group("number")
    year = int(number.split("/")[-1])
    return number, 2000 + year if year < 80 else 1900 + year


def almar_record_from_feed_item(item: FeedItem) -> MessageRecord:
    number, fiscal_year = parse_almar_number(f"{item.title}\n{item.summary or ''}")
    if number:
        source_id = f"almar-{number.replace('/', '-')}"
        warnings: list[str] = []
    else:
        source_id = f"almar-{hashlib.sha256(item.link.encode('utf-8')).hexdigest()[:16]}"
        warnings = ["Could not parse ALMAR message number from the feed entry."]
    source_hash = hashlib.sha256(f"{item.title}\n{item.link}\n{item.summary or ''}".encode()).hexdigest()
    return MessageRecord(
        source_id=source_id,
        title=item.title,
        canonical_url=item.link,
        message_number=number,
        fiscal_year=fiscal_year,
        published_at=item.published_at,
        summary=item.summary,
        tags=tag_message(item),
        source_family="ALMAR",
        status="official_message",
        source_hash=source_hash,
        parser_warnings=warnings,
    )
