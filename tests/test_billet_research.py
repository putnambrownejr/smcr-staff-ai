"""Tests for billet research service, store, and route."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.staff.billet_research_service import build_research_note
from app.services.staff.billet_research_store import BilletResearchStore


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------

def test_build_research_note_infantry_s3() -> None:
    note = build_research_note("testuser", "S-3", "4th MarDiv", "0302")
    assert "# Billet Research" in note
    assert "S-3" in note
    assert "Infantry" in note
    assert "4th Marine Division" in note
    assert "UNCLASSIFIED" in note


def test_build_research_note_suppo() -> None:
    note = build_research_note("testuser", "SuppO", "", "3041")
    assert "Supply Officer" in note
    assert "MCO 4400.16" in note
    assert "Supply" in note


def test_build_research_note_unknown_billet_and_mos() -> None:
    note = build_research_note("testuser", "XO", "2nd MarDiv", "")
    assert "Executive Officer" in note
    assert "SMCR Training Context" in note


def test_build_research_note_empty_inputs() -> None:
    note = build_research_note("testuser", "", "", "")
    assert "UNCLASSIFIED" in note
    assert "SMCR Training Context" in note


# ---------------------------------------------------------------------------
# Store unit tests
# ---------------------------------------------------------------------------

def test_store_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = BilletResearchStore(tmp)
        content = "# Test Research\n- Item one\n"
        store.upsert("mykey", content)
        assert store.get("mykey") == content


def test_store_get_missing_returns_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = BilletResearchStore(tmp)
        assert store.get("nobody") is None


def test_store_delete() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = BilletResearchStore(tmp)
        store.upsert("mykey", "# content")
        store.delete("mykey")
        assert store.get("mykey") is None


def test_store_invalid_key_raises() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = BilletResearchStore(tmp)
        with pytest.raises(ValueError, match="Invalid user_key"):
            store.upsert("../../../etc/passwd", "bad")


# ---------------------------------------------------------------------------
# Route integration tests
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("USER_PROFILE_STORAGE_DIR", str(tmp_path / "profiles"))
    monkeypatch.setenv("BILLET_RESEARCH_STORAGE_DIR", str(tmp_path / "research"))
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.services.staff.user_profile_store import UserProfileStore
    store = UserProfileStore(str(tmp_path / "profiles"))
    store.upsert("alice", billet="S-3", unit="4th MarDiv", mos="0302")
    yield TestClient(app)
    get_settings.cache_clear()


def test_research_404_before_generate(client: TestClient) -> None:
    resp = client.get("/user-profile/alice/research")
    assert resp.status_code == 404


def test_research_generate_and_retrieve(client: TestClient) -> None:
    resp = client.post("/user-profile/alice/research")
    assert resp.status_code == 200
    text = resp.text
    assert "UNCLASSIFIED" in text
    assert "S-3" in text

    resp2 = client.get("/user-profile/alice/research")
    assert resp2.status_code == 200
    assert resp2.text == text


def test_research_generate_no_profile(client: TestClient) -> None:
    resp = client.post("/user-profile/noone/research")
    assert resp.status_code == 404


def test_research_generate_empty_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_PROFILE_STORAGE_DIR", str(tmp_path / "profiles"))
    monkeypatch.setenv("BILLET_RESEARCH_STORAGE_DIR", str(tmp_path / "research"))
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.services.staff.user_profile_store import UserProfileStore
    store = UserProfileStore(str(tmp_path / "profiles"))
    store.upsert("empty_user", billet="", unit="", mos="")
    c = TestClient(app)
    resp = c.post("/user-profile/empty_user/research")
    assert resp.status_code == 422
    get_settings.cache_clear()
