from typing import Protocol

from app.schemas.ingestion import MessageRecord
from app.services.ingestion.maradmin_feed_store import MaradminFeedStore
from app.services.ingestion.maradmin_scraper import normalize_message_records
from app.services.ingestion.rss_client import FeedItem, RssClient

OFFICIAL_MARADMIN_RSS_URL = (
    "https://www.marines.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=6&Site=481&category=14336&max=10"
)


class RssClientLike(Protocol):
    def fetch_sync(self, url: str) -> list[FeedItem]: ...


class MaradminFeedService:
    def __init__(
        self,
        rss_client: RssClientLike | None = None,
        feed_url: str = OFFICIAL_MARADMIN_RSS_URL,
    ) -> None:
        self.rss_client = rss_client or RssClient()
        self.feed_url = feed_url

    def refresh(self, store: MaradminFeedStore) -> list[MessageRecord]:
        items = self.rss_client.fetch_sync(self.feed_url)
        records = normalize_message_records(items)
        return store.save_many(records)
