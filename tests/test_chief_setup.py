"""Tests for the Chief of Staff setup store, briefing block, and routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.chief_setup import ChiefSetup, ChiefSetupUpsertRequest
from app.services.chief.setup_store import (
    ChiefSetupStore,
    build_chief_briefing_block,
    is_configured,
)


@pytest.fixture()
def setup_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = tmp_path / "chief_setup"
    monkeypatch.setattr(get_settings(), "chief_setup_storage_dir", str(d))
    return d


def test_store_round_trips_and_cleans_lists(setup_dir: Path) -> None:
    store = ChiefSetupStore(setup_dir)
    request = ChiefSetupUpsertRequest(
        unit="4th CAG",
        billet="S-4A",
        priorities=["Close RQS gaps", "  ", "Close RQS gaps", "FitReps by 31 AUG"],
        watch_items=[""],
    )
    setup = store.upsert("user-a", request)

    # Blank and duplicate list items are dropped.
    assert setup.priorities == ["Close RQS gaps", "FitReps by 31 AUG"]
    assert setup.watch_items == []
    loaded = store.get("user-a")
    assert loaded is not None
    assert loaded.unit == "4th CAG"


def test_is_configured_flips_on_meaningful_content(setup_dir: Path) -> None:
    assert is_configured(None) is False
    assert is_configured(ChiefSetup(user_key="x")) is False
    assert is_configured(ChiefSetup(user_key="x", unit="4th CAG")) is True


def test_briefing_block_includes_context_and_safety_footer() -> None:
    setup = ChiefSetup(
        user_key="x",
        unit="4th CAG",
        billet="S-4A",
        priorities=["Close RQS gaps"],
        battle_rhythm=["0730 COC sync"],
        watch_items=["AT budget MARADMIN"],
        output_format="Bullet",
    )
    block = build_chief_briefing_block(setup)
    assert "You are my Chief of Staff" in block
    assert "4th CAG" in block
    assert "Close RQS gaps" in block
    assert "0730 COC sync" in block
    assert "Default output format for drafts: Bullet" in block
    assert "UNCLASSIFIED only" in block


def test_routes_get_default_then_upsert(setup_dir: Path) -> None:
    client = TestClient(app)

    empty = client.get("/chief-setup/user-b")
    assert empty.status_code == 200
    assert empty.json()["is_configured"] is False

    saved = client.put(
        "/chief-setup/user-b",
        json={"unit": "2/24", "commander_intent": "Rebuild the bench", "priorities": ["Drill prep"]},
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["is_configured"] is True
    assert body["setup"]["unit"] == "2/24"
    assert "Rebuild the bench" in body["briefing_block"]

    # Round-trips on a fresh GET.
    again = client.get("/chief-setup/user-b")
    assert again.json()["setup"]["unit"] == "2/24"


def test_delete_route(setup_dir: Path) -> None:
    client = TestClient(app)
    client.put("/chief-setup/user-c", json={"unit": "H&S Co"})
    assert client.delete("/chief-setup/user-c").status_code == 204
    assert client.delete("/chief-setup/user-c").status_code == 404
