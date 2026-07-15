from datetime import date
from pathlib import Path

import yaml
from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from app.api.routes.dashboard import get_history_service
from app.main import app
from app.schemas.history import HistoryScope, TodayInMarineHistoryItem
from app.services.history.catalog import BUNDLED_HISTORY_PATHS
from app.services.history.local_history_store import LocalHistoryStore
from app.services.history.today_in_history import TodayInMarineHistoryService, extract_history_items_from_markdown


def _history_item(
    slug: str,
    month: int,
    day: int,
    scope: HistoryScope,
    *,
    year_label: str = "2000",
) -> TodayInMarineHistoryItem:
    return TodayInMarineHistoryItem(
        slug=slug,
        title=slug.replace("-", " ").title(),
        month=month,
        day=day,
        year_label=year_label,
        summary=f"Summary for {slug}.",
        scope=scope,
        references=["https://example.mil/history"],
    )


def test_extract_history_items_from_markdown_parses_dated_entries() -> None:
    markdown = """
- **November 10, 1775 – Marine Corps Birthday:** The Continental Congress resolved to raise two battalions of Marines.
- **Feb 19, 1945** – *Flag raised on Iwo Jima.* Marines captured Suribachi.
"""

    items = extract_history_items_from_markdown(markdown, "test-source")

    assert len(items) == 2
    assert any(item.month == 11 and item.day == 10 and item.year_label == "1775" for item in items)
    assert any("test-source" in item.references for item in items)


def test_dashboard_history_service_merges_seed_and_local_items(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.yaml"
    local_path = tmp_path / "local.yaml"
    seed_path.write_text(
        "items:\n"
        "  - slug: seed-item\n"
        "    title: Seed item\n"
        "    month: 1\n"
        "    day: 1\n"
        "    year_label: '1900'\n"
        "    summary: Seed summary\n"
        "    significance: []\n"
        "    references: []\n",
        encoding="utf-8",
    )
    local_path.write_text(
        "items:\n"
        "  - slug: local-item\n"
        "    title: Local item\n"
        "    month: 1\n"
        "    day: 1\n"
        "    year_label: '1950'\n"
        "    summary: Local summary\n"
        "    significance: []\n"
        "    references: []\n",
        encoding="utf-8",
    )

    service = TodayInMarineHistoryService.from_paths([seed_path, local_path])

    items = service.get_for_date(date(2026, 1, 1))
    assert {item.slug for item in items} == {"seed-item", "local-item"}


def test_history_selector_prefers_exact_event_within_scope() -> None:
    service = TodayInMarineHistoryService(
        [
            _history_item("near-usmc", 7, 14, HistoryScope.usmc),
            _history_item("exact-usmc", 7, 15, HistoryScope.usmc),
            _history_item("exact-military", 7, 15, HistoryScope.us_military),
        ]
    )

    marine = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)
    military = service.select_for_date(date(2026, 7, 15), HistoryScope.us_military)

    assert marine is not None and marine.item.slug == "exact-usmc"
    assert marine.is_exact is True and marine.distance_days == 0
    assert military is not None and military.item.slug == "exact-military"


def test_history_selector_uses_previous_event_for_equal_distance_tie() -> None:
    service = TodayInMarineHistoryService(
        [
            _history_item("previous", 7, 14, HistoryScope.usmc),
            _history_item("following", 7, 16, HistoryScope.usmc),
        ]
    )

    selected = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)

    assert selected is not None and selected.item.slug == "previous"
    assert selected.is_exact is False and selected.distance_days == 1


def test_history_selector_wraps_across_year_boundary() -> None:
    service = TodayInMarineHistoryService(
        [
            _history_item("new-years-day", 1, 1, HistoryScope.us_military),
            _history_item("farther", 12, 20, HistoryScope.us_military),
        ]
    )

    selected = service.select_for_date(date(2026, 12, 31), HistoryScope.us_military)

    assert selected is not None and selected.item.slug == "new-years-day"
    assert selected.distance_days == 1


def test_history_selector_returns_none_for_empty_scope() -> None:
    service = TodayInMarineHistoryService(
        [_history_item("marine-only", 7, 15, HistoryScope.usmc)]
    )

    assert service.select_for_date(date(2026, 7, 15), HistoryScope.us_military) is None


def test_history_selector_returns_none_when_both_scopes_are_empty() -> None:
    service = TodayInMarineHistoryService([])

    assert service.select_for_date(date(2026, 7, 15), HistoryScope.usmc) is None
    assert service.select_for_date(date(2026, 7, 15), HistoryScope.us_military) is None


def test_history_selector_breaks_same_date_ties_by_year_then_slug() -> None:
    service = TodayInMarineHistoryService(
        [
            _history_item("zulu", 7, 15, HistoryScope.usmc, year_label="1918"),
            _history_item("alpha", 7, 15, HistoryScope.usmc, year_label="1918"),
            _history_item("older", 7, 15, HistoryScope.usmc, year_label="1775"),
        ]
    )

    selected = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)

    assert selected is not None and selected.item.slug == "older"


def test_legacy_history_record_defaults_to_usmc_scope() -> None:
    item = TodayInMarineHistoryItem.model_validate(
        {
            "slug": "legacy",
            "title": "Legacy Marine event",
            "month": 1,
            "day": 1,
            "year_label": "1900",
            "summary": "Stored before scope metadata existed.",
            "references": ["local-history"],
        }
    )

    assert item.scope is HistoryScope.usmc


def test_history_store_round_trips_scope_as_yaml_string(tmp_path: Path) -> None:
    store = LocalHistoryStore(tmp_path / "history")

    store.replace([_history_item("army", 6, 14, HistoryScope.us_military)])

    raw = yaml.safe_load(store.path.read_text(encoding="utf-8"))
    assert raw["items"][0]["scope"] == "us_military"
    assert store.list_items()[0].scope is HistoryScope.us_military


def test_history_service_skips_malformed_local_catalog(tmp_path: Path) -> None:
    valid_path = tmp_path / "valid.yaml"
    invalid_path = tmp_path / "invalid.yaml"
    valid_path.write_text(
        yaml.safe_dump(
            {
                "items": [
                    _history_item("valid", 1, 1, HistoryScope.usmc).model_dump(mode="json")
                ]
            }
        ),
        encoding="utf-8",
    )
    invalid_path.write_text("items: [not: valid: yaml", encoding="utf-8")

    service = TodayInMarineHistoryService.from_paths([valid_path, invalid_path])

    assert [item.slug for item in service.list_items()] == ["valid"]


def test_seed_history_includes_july_14_event() -> None:
    service = TodayInMarineHistoryService.from_yaml(
        Path("data/seed/usmc_history_on_this_day.example.yaml")
    )

    items = service.get_for_date(date(2026, 7, 14))

    assert any(item.slug == "uss-iwo-jima-decommissioned" for item in items)


def test_bundled_history_catalogs_have_scopes_and_sources() -> None:
    seen_scopes: set[HistoryScope] = set()
    for path in BUNDLED_HISTORY_PATHS:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        assert payload.get("items"), f"No history items in {path}"
        for raw_item in payload["items"]:
            assert "scope" in raw_item, f"Missing explicit scope for {raw_item.get('slug')}"
            item = TodayInMarineHistoryItem.model_validate(raw_item)
            assert item.references, f"Missing source for {item.slug}"
            assert all(reference.startswith("https://") for reference in item.references)
            seen_scopes.add(item.scope)
    assert seen_scopes == {HistoryScope.usmc, HistoryScope.us_military}


def test_markdown_import_preserves_requested_scope() -> None:
    markdown = (
        "- **July 15, 1918 – Rock of the Marne:** "
        "The 38th Infantry held its position."
    )

    items = extract_history_items_from_markdown(
        markdown,
        "https://history.army.mil/",
        HistoryScope.us_military,
    )

    assert len(items) == 1
    assert items[0].scope is HistoryScope.us_military


def test_history_import_route_saves_local_history(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    markdown_path = tmp_path / "history.md"
    markdown_path.write_text(
        (
            "- **November 10, 1775 – Marine Corps Birthday:** "
            "The Continental Congress resolved to raise two battalions of Marines.\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SMCR_STAFF_AI_HOME", str(tmp_path / "state"))
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        client = TestClient(app)
        response = client.post(
            "/history/import-markdown",
            json={
                "markdown_paths": [str(markdown_path)],
                "replace_existing": True,
                "scope": "us_military",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["imported_count"] == 1
        assert payload["total_available"] == 1
        history_service = get_history_service()
        assert any(
            item.slug.startswith("11-10-1775")
            for item in history_service.get_for_date(date(2026, 11, 10))
        )
        imported = next(
            item
            for item in history_service.get_for_date(date(2026, 11, 10))
            if item.slug.startswith("11-10-1775")
        )
        assert imported.scope is HistoryScope.us_military
    finally:
        get_settings.cache_clear()
