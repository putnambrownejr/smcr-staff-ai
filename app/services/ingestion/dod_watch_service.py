from __future__ import annotations

import hashlib
from typing import Protocol

from app.schemas.ingestion import MessageRecord
from app.schemas.message_watch import MessageWatchRefreshResponse
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.rss_client import FeedItem, RssClient

OFFICIAL_DOD_RELEASES_RSS_URL = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=9&Site=945&max=10"

_HIGH_SIGNAL_KEYWORDS = {
    "reserve",
    "readiness",
    "training",
    "education",
    "policy",
    "secretary",
    "deputy",
    "personnel",
    "travel",
    "safety",
    "health",
    "cyber",
    "software",
    "records",
    "artificial intelligence",
    "ai",
    "force",
    "marines",
    "navy",
}


class RssClientLike(Protocol):
    def fetch_sync(self, url: str) -> list[FeedItem]: ...


class DodWatchService:
    def __init__(
        self,
        rss_client: RssClientLike | None = None,
        feed_url: str = OFFICIAL_DOD_RELEASES_RSS_URL,
    ) -> None:
        self.rss_client = rss_client or RssClient()
        self.feed_url = feed_url

    def refresh(self, store: MessageRecordStore) -> MessageWatchRefreshResponse:
        items = self.rss_client.fetch_sync(self.feed_url)
        records = [_to_record(item) for item in items if _is_high_signal(item)]
        return MessageWatchRefreshResponse(records=store.save_many(records))


def _is_high_signal(item: FeedItem) -> bool:
    haystack = f"{item.title} {item.summary or ''}".lower()
    return any(keyword in haystack for keyword in _HIGH_SIGNAL_KEYWORDS)


def _to_record(item: FeedItem) -> MessageRecord:
    source_hash = hashlib.sha256(f"{item.title}\n{item.link}\n{item.summary or ''}".encode()).hexdigest()
    return MessageRecord(
        source_id=f"dod-{hashlib.sha256(item.link.encode('utf-8')).hexdigest()[:16]}",
        title=item.title,
        canonical_url=item.link,
        published_at=item.published_at,
        summary=item.summary,
        tags=_tags(item),
        source_family="DOD_RELEASE",
        status="official_release",
        source_hash=source_hash,
    )


def _tags(item: FeedItem) -> list[str]:
    haystack = f"{item.title} {item.summary or ''}".lower()
    tags: list[str] = []
    tag_map = {
        "Readiness": ("readiness", "force"),
        "Policy": ("policy", "memo", "directive"),
        "Training": ("training", "education"),
        "Personnel": ("personnel", "assignment"),
        "Technology": ("software", "artificial intelligence", "ai", "cyber"),
        "Safety": ("safety", "health"),
        "Travel": ("travel",),
    }
    for tag, keywords in tag_map.items():
        if any(keyword in haystack for keyword in keywords):
            tags.append(tag)
    return tags or ["DoD"]
