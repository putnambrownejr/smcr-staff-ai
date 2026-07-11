"""Tests for the handoff creation path and its effect on /dashboard/data/{user_key}."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.handoffs import get_handoff_store
from app.core.config import get_settings
from app.main import app
from app.services.session.handoff_store import SessionHandoffStore


@pytest.fixture()
def dashboard_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    store = SessionHandoffStore(tmp_path / "handoffs")
    monkeypatch.setenv("LOCAL_CONTEXT_STORAGE_DIR", str(tmp_path / "context"))
    monkeypatch.setenv("SESSION_HANDOFF_STORAGE_DIR", str(tmp_path / "handoffs"))
    monkeypatch.setenv("USER_PROFILE_STORAGE_DIR", str(tmp_path / "profiles"))
    monkeypatch.setenv("BENCH_SECTIONS_STORAGE_DIR", str(tmp_path / "bench"))
    get_settings.cache_clear()
    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_handoff_store, None)
    get_settings.cache_clear()


def test_create_handoff_then_appears_in_dashboard(dashboard_client: TestClient) -> None:
    user_key = "test-user"

    # No handoff yet — dashboard still works, chief_brief is advisory
    resp = dashboard_client.get(f"/dashboard/data/{user_key}")
    assert resp.status_code == 200
    data = resp.json()
    chief = data.get("chief_brief") or {}
    top = chief.get("top_priority_items") or []
    titles = [a["title"] for a in top]
    assert any("handoff" in t.lower() for t in titles), (
        f"Expected a 'create handoff' priority item before handoff exists; got: {titles}"
    )

    # Create the handoff via PUT /handoffs/{user_key}
    put_resp = dashboard_client.put(
        f"/handoffs/{user_key}",
        json={
            "user_key": user_key,
            "display_name": "Capt Test",
            "rank": "CPT",
            "admin_watch_items": ["PME deadline", "FitRep due"],
            "recurring_drill_notes": ["Check ammo account"],
        },
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["handoff"]["display_name"] == "Capt Test"

    # Dashboard now reflects the handoff — no longer prompts for creation
    resp2 = dashboard_client.get(f"/dashboard/data/{user_key}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    top2 = (data2.get("chief_brief") or {}).get("top_priority_items") or []
    titles2 = [a["title"] for a in top2]
    assert not any(
        t.lower() == "create or update session handoff" for t in titles2
    ), "Expected handoff creation prompt to disappear after handoff is saved"


def test_handoff_round_trip(dashboard_client: TestClient) -> None:
    user_key = "round-trip"
    body = {
        "user_key": user_key,
        "rank": "MAJ",
        "admin_watch_items": ["Item A", "Item B"],
    }
    put = dashboard_client.put(f"/handoffs/{user_key}", json=body)
    assert put.status_code == 200

    get = dashboard_client.get(f"/handoffs/{user_key}")
    assert get.status_code == 200
    saved = get.json()
    assert saved["rank"] == "MAJ"
    assert saved["admin_watch_items"] == ["Item A", "Item B"]
