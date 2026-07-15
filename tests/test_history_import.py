from datetime import date
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from app.api.routes.dashboard import get_history_service
from app.main import app
from app.services.history.today_in_history import TodayInMarineHistoryService, extract_history_items_from_markdown


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


def test_seed_history_includes_july_14_event() -> None:
    service = TodayInMarineHistoryService.from_yaml(
        Path("data/seed/usmc_history_on_this_day.example.yaml")
    )

    items = service.get_for_date(date(2026, 7, 14))

    assert any(item.slug == "uss-iwo-jima-decommissioned" for item in items)


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
            json={"markdown_paths": [str(markdown_path)], "replace_existing": True},
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
    finally:
        get_settings.cache_clear()
