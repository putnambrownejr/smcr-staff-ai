from datetime import UTC, datetime
from pathlib import Path

from app.services.ingestion.dod_watch_service import DodWatchService
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.rss_client import FeedItem


class _FakeRssClient:
    def fetch_sync(self, url: str) -> list[FeedItem]:
        return [
            FeedItem(
                title="Deputy Secretary Issues Readiness and AI Guidance",
                link="https://www.defense.gov/example-guidance",
                published_at=datetime(2026, 5, 18, tzinfo=UTC),
                summary="Policy update touching readiness, artificial intelligence, and training.",
            ),
            FeedItem(
                title="Community event at installation museum",
                link="https://www.defense.gov/example-fyi",
                published_at=datetime(2026, 5, 17, tzinfo=UTC),
                summary="A low-signal human-interest item.",
            ),
        ]


def test_dod_watch_refresh_filters_for_high_signal_items(tmp_path: Path) -> None:
    store = MessageRecordStore(tmp_path / "dod_watch")
    service = DodWatchService(rss_client=_FakeRssClient())

    response = service.refresh(store)

    assert not response.warnings
    assert len(response.records) == 1
    assert response.records[0].source_family == "DOD_RELEASE"
    assert response.records[0].title == "Deputy Secretary Issues Readiness and AI Guidance"
