from __future__ import annotations

import hashlib
from typing import Protocol

from app.schemas.custom_watch_feeds import CustomWatchFeed, CustomWatchFeedRefreshResponse
from app.schemas.ingestion import MessageRecord
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.rss_client import FeedItem, RssClient


class RssClientLike(Protocol):
    def fetch_sync(self, url: str) -> list[FeedItem]: ...


class CustomWatchFeedService:
    def __init__(self, rss_client: RssClientLike | None = None) -> None:
        self.rss_client = rss_client or RssClient()

    def refresh(
        self,
        *,
        feed: CustomWatchFeed,
        store: CustomWatchFeedStore,
    ) -> CustomWatchFeedRefreshResponse:
        warnings: list[str] = []
        if not feed.enabled:
            warnings.append("Feed is disabled. Enable it before refresh if you want fresh items.")
            return CustomWatchFeedRefreshResponse(feed=feed, records=[], warnings=warnings)

        item_store = MessageRecordStore(store.items_path(feed.feed_id))
        try:
            items = self.rss_client.fetch_sync(str(feed.url))
            records = [_to_record(feed, item) for item in items]
            saved = item_store.save_many(records)
            updated = store.mark_refresh(feed.feed_id, item_count=len(saved), error=None) or feed
            return CustomWatchFeedRefreshResponse(feed=updated, records=saved, warnings=warnings)
        except Exception as exc:
            message = f"Refresh failed: {exc}"
            updated = store.mark_refresh(feed.feed_id, item_count=0, error=message) or feed
            warnings.append(message)
            return CustomWatchFeedRefreshResponse(
                feed=updated,
                records=item_store.list(limit=25),
                warnings=warnings,
            )

    def list_items(self, *, feed: CustomWatchFeed, store: CustomWatchFeedStore, limit: int = 25) -> list[MessageRecord]:
        item_store = MessageRecordStore(store.items_path(feed.feed_id))
        return item_store.list(limit=limit)


def _to_record(feed: CustomWatchFeed, item: FeedItem) -> MessageRecord:
    source_hash = hashlib.sha256(f"{item.title}\n{item.link}\n{item.summary or ''}".encode()).hexdigest()
    source_id = hashlib.sha256(f"{feed.feed_id}|{item.link}".encode()).hexdigest()[:16]
    tags = [feed.category, feed.trust_level.value, *feed.tags]
    return MessageRecord(
        source_id=f"custom-feed-{source_id}",
        title=item.title,
        canonical_url=item.link,
        published_at=item.published_at,
        summary=item.summary,
        tags=tags,
        source_family=f"CUSTOM_RSS_{feed.trust_level.value.upper()}",
        status="custom_feed",
        source_hash=source_hash,
    )
