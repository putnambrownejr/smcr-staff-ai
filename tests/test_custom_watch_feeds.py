from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.custom_watch_feeds import CreateCustomWatchFeedRequest
from app.services.ingestion.custom_watch_feed_service import CustomWatchFeedService
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore
from app.services.ingestion.rss_client import FeedItem


class _FakeRssClient:
    def fetch_sync(self, url: str) -> list[FeedItem]:
        return [
            FeedItem(
                title="Official unit bulletin",
                link="https://example.test/unit-bulletin",
                published_at=datetime(2026, 5, 18, tzinfo=UTC),
                summary="Reserve-focused official unit update.",
            )
        ]


def test_custom_watch_feed_store_and_service_refresh(tmp_path: Path) -> None:
    store = CustomWatchFeedStore(tmp_path / "custom_feeds")
    feed = store.create(
        CreateCustomWatchFeedRequest(
            name="Unit updates",
            url="https://example.test/feed.xml",
            category="unit_news",
            trust_level="official",
            tags=["reserve", "training"],
        )
    )
    response = CustomWatchFeedService(rss_client=_FakeRssClient()).refresh(feed=feed, store=store)

    assert not response.warnings
    assert response.records[0].title == "Official unit bulletin"
    assert response.records[0].tags[:2] == ["unit_news", "official"]
    assert response.feed.last_item_count == 1


def test_custom_watch_feed_routes_crud_and_items(tmp_path: Path) -> None:
    from app.api.routes.custom_watch_feeds import get_feed_service, get_feed_store

    store = CustomWatchFeedStore(tmp_path / "custom_feeds")

    def override_store() -> CustomWatchFeedStore:
        return store

    def override_service() -> CustomWatchFeedService:
        return CustomWatchFeedService(rss_client=_FakeRssClient())

    app.dependency_overrides[get_feed_store] = override_store
    app.dependency_overrides[get_feed_service] = override_service

    client = TestClient(app)
    try:
        create = client.post(
            "/custom-watch-feeds",
            json={
                "name": "Unit updates",
                "url": "https://example.test/feed.xml",
                "category": "unit_news",
                "trust_level": "official",
                "tags": ["reserve"],
            },
        )
        assert create.status_code == 200
        feed_id = create.json()["feed_id"]

        refresh = client.post(f"/custom-watch-feeds/{feed_id}/refresh")
        assert refresh.status_code == 200
        assert refresh.json()["records"][0]["title"] == "Official unit bulletin"

        items = client.get(f"/custom-watch-feeds/{feed_id}/items")
        assert items.status_code == 200
        assert items.json()[0]["source_family"] == "CUSTOM_RSS_OFFICIAL"

        patch = client.patch(f"/custom-watch-feeds/{feed_id}", json={"enabled": False})
        assert patch.status_code == 200
        assert patch.json()["enabled"] is False
    finally:
        app.dependency_overrides.clear()
