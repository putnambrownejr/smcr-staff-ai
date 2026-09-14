"""ALMAR feed: number parsing from the RSS header, honest failure, and the message-watch routes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes.message_watch import get_almar_service, get_almar_store
from app.main import app
from app.services.ingestion.almar_feed_service import AlmarFeedService, almar_record_from_feed_item, parse_almar_number
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.ingestion.rss_client import FeedItem

_ITEMS = [
    FeedItem(
        title="LABOR DAY MESSAGE 2026",
        link="https://www.marines.mil/News/Messages/Messages-Display/Article/4590917/labor-day-message-2026/",
        published_at=datetime(2026, 9, 3, 21, 6, 59, tzinfo=UTC),
        summary="R 032026Z SEP 26ALMAR 021/26MSGID/CMC WASHINGTON DC//SUBJ/LABOR DAY MESSAGE 2026//GENTEXT/REMARKS/<br />",
    ),
    FeedItem(
        title="SERGEANTS MAJOR SLATE 1-27",
        link="https://www.marines.mil/News/Messages/Messages-Display/Article/4558974/sergeants-major-slate-1-27/",
        published_at=datetime(2026, 7, 30, 10, 58, 42, tzinfo=UTC),
        summary="R 291630Z JUL 26ALMAR 018/26MSGID/GENADMIN/CMC WASHINGTON DC//SUBJ/SERGEANTS MAJOR SLATE<br />",
    ),
    FeedItem(title="UNNUMBERED ENTRY", link="https://www.marines.mil/x/", summary="No header here."),
]


class _FakeRss:
    def __init__(self, items: list[FeedItem] | None = None, error: Exception | None = None) -> None:
        self.items = items or []
        self.error = error

    def fetch_sync(self, url: str) -> list[FeedItem]:
        if self.error is not None:
            raise self.error
        return list(self.items)


def test_parse_almar_number_reads_the_message_header() -> None:
    assert parse_almar_number("R 032026Z SEP 26ALMAR 021/26MSGID/CMC") == ("021/26", 2026)
    assert parse_almar_number("nothing") == (None, None)


def test_record_carries_number_family_and_stable_id() -> None:
    record = almar_record_from_feed_item(_ITEMS[0])
    assert record.source_id == "almar-021-26"
    assert record.message_number == "021/26"
    assert record.fiscal_year == 2026
    assert record.source_family == "ALMAR"
    assert record.status == "official_message"
    assert record.parser_warnings == []
    unnumbered = almar_record_from_feed_item(_ITEMS[2])
    assert unnumbered.source_id.startswith("almar-")
    assert unnumbered.message_number is None
    assert unnumbered.parser_warnings


def test_refresh_saves_records_and_reports_failures_honestly(tmp_path: Path) -> None:
    store = MessageRecordStore(tmp_path / "almars")
    ok = AlmarFeedService(rss_client=_FakeRss(_ITEMS)).refresh(store)
    # The store sorts by published_at, falling back to retrieved_at, so the unnumbered entry floats first.
    assert sorted(str(record.message_number) for record in ok.records) == ["018/26", "021/26", "None"]
    assert ok.warnings == []

    request = httpx.Request("GET", "https://www.marines.mil/rss")
    response = httpx.Response(403, request=request)
    blocked = AlmarFeedService(rss_client=_FakeRss(error=httpx.HTTPStatusError("blocked", request=request, response=response)))
    result = blocked.refresh(store)
    assert result.warnings and "HTTP 403" in result.warnings[0]
    assert len(result.records) == 3  # cached data still served


@pytest.fixture()
def almar_client(tmp_path: Path) -> Iterator[TestClient]:
    store = MessageRecordStore(tmp_path / "almars")
    app.dependency_overrides[get_almar_store] = lambda: store
    app.dependency_overrides[get_almar_service] = lambda: AlmarFeedService(rss_client=_FakeRss(_ITEMS))
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_almar_store, None)
        app.dependency_overrides.pop(get_almar_service, None)


def test_message_watch_routes_serve_almars_and_drop_navadmin(almar_client: TestClient) -> None:
    refreshed = almar_client.post("/message-watch/almars/refresh")
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["warnings"] == []
    feed = almar_client.get("/message-watch/almars/feed").json()
    labor_day = next(item for item in feed if item["message_number"] == "021/26")
    assert labor_day["source_family"] == "ALMAR"
    assert labor_day["title"] == "LABOR DAY MESSAGE 2026"
    assert almar_client.get("/message-watch/navadmins/feed").status_code == 404
    assert almar_client.post("/message-watch/alnavs/refresh").status_code == 404
