from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.schemas.ingestion import MessageRecord
from app.services.ingestion.maradmin_feed_service import MaradminFeedService
from app.services.ingestion.maradmin_feed_store import MAX_FEED_ENTRIES, MaradminFeedStore
from app.services.ingestion.rss_client import FeedItem, parse_feed


class _FakeRssClient:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def fetch_sync(self, url: str) -> list[FeedItem]:
        return parse_feed(self.fixture_path.read_text(encoding="utf-8"))


def test_maradmin_feed_service_refreshes_and_caches_records(tmp_path: Path) -> None:
    store = MaradminFeedStore(tmp_path / "maradmin_feed")
    service = MaradminFeedService(
        rss_client=_FakeRssClient(Path("tests/fixtures/sample_maradmin_feed.xml")),
        feed_url="https://example.test/maradmin.xml",
    )

    records = service.refresh(store)

    assert len(records) == 2
    titles = {record.title for record in records}
    assert "Reserve Officer PME Training Update" in titles
    assert all(record.canonical_url for record in records)
    assert store.list(limit=10)[0].source_id.startswith("maradmin-")


def test_maradmin_feed_store_trims_to_newest_entries(tmp_path: Path) -> None:
    store = MaradminFeedStore(tmp_path / "maradmin_feed")
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    records = [
        MessageRecord(
            source_id=f"maradmin-{index}",
            title=f"MARADMIN {index}",
            canonical_url=f"https://example.test/maradmin/{index}",
            published_at=base_time + timedelta(days=index),
        )
        for index in range(MAX_FEED_ENTRIES + 5)
    ]

    saved = store.save_many(records)
    stored = store.list()

    assert len(saved) == MAX_FEED_ENTRIES
    assert len(stored) == MAX_FEED_ENTRIES
    assert stored[0].source_id == f"maradmin-{MAX_FEED_ENTRIES + 4}"
    assert store.get("maradmin-0") is None
