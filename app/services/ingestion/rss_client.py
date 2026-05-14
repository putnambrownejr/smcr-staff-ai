from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from pydantic import BaseModel


class FeedItem(BaseModel):
    title: str
    link: str
    published_at: datetime | None = None
    summary: str | None = None


class RssClient:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch(self, url: str) -> list[FeedItem]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url)
            response.raise_for_status()
        return parse_feed(response.text)


def parse_feed(xml_text: str) -> list[FeedItem]:
    parsed = feedparser.parse(xml_text)
    items: list[FeedItem] = []
    for entry in parsed.entries:
        published_at = None
        raw_date = entry.get("published") or entry.get("updated")
        if raw_date:
            try:
                published_at = parsedate_to_datetime(raw_date)
            except (TypeError, ValueError):
                published_at = None
        items.append(
            FeedItem(
                title=str(entry.get("title", "")),
                link=str(entry.get("link", "")),
                published_at=published_at,
                summary=str(entry.get("summary", "")) or None,
            )
        )
    return items
