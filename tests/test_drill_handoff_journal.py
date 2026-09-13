from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.handoffs import get_handoff_store
from app.core.config import get_settings
from app.main import app
from app.schemas.session import UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


@pytest.fixture()
def journal_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("LOCAL_API_KEY", "journal-test")
    get_settings.cache_clear()
    store = SessionHandoffStore(tmp_path)
    app.dependency_overrides[get_handoff_store] = lambda: store
    try:
        yield TestClient(app, headers={"X-Local-API-Key": "journal-test"})
    finally:
        app.dependency_overrides.pop(get_handoff_store, None)
        get_settings.cache_clear()


def test_journal_preserves_profile_and_updates_summary(journal_client: TestClient) -> None:
    url = "/handoffs/journal-user"
    assert journal_client.put(url, json={"user_key": "journal-user", "rank": "Capt", "preferences": {"format": "bullet"}}).status_code == 200
    entries = [
        {"id": "new", "label": "Next drill", "admin": "Review draft\n\nConfirm dates", "drill": "Bring notebook"},
        {"id": "old", "label": "Previous drill", "admin": "Old item", "archived": True},
    ]
    saved = journal_client.patch(url + "/journal", json={"entries": entries})
    assert saved.status_code == 200
    loaded = journal_client.get(url).json()
    assert loaded["rank"] == "Capt"
    assert loaded["preferences"] == {"format": "bullet"}
    assert len(loaded["drill_handoffs"]) == 2
    assert loaded["admin_watch_items"] == ["Review draft", "Confirm dates"]
    assert loaded["recurring_drill_notes"] == ["Bring notebook"]
    assert loaded["drill_handoffs"][1]["archived"] is True


def test_empty_journal_survives_reload_without_legacy_resurrection(journal_client: TestClient) -> None:
    url = "/handoffs/journal-user"
    journal_client.put(url, json={"user_key": "journal-user", "admin_watch_items": ["Legacy note"]})
    assert journal_client.get(url).json()["drill_handoffs"] is None
    assert journal_client.patch(url + "/journal", json={"entries": []}).status_code == 200
    loaded = journal_client.get(url).json()
    assert loaded["drill_handoffs"] == []
    assert loaded["admin_watch_items"] == []
    assert loaded["recurring_drill_notes"] == []


def test_journal_rejects_duplicate_ids_and_requires_auth(journal_client: TestClient) -> None:
    url = "/handoffs/journal-user/journal"
    assert journal_client.patch(url, json={"entries": [{"id": "one"}, {"id": "one"}]}).status_code == 422
    assert journal_client.patch(url, json={"entries": []}, headers={"X-Local-API-Key": "wrong"}).status_code == 401


def test_legacy_profile_update_keeps_saved_journal(journal_client: TestClient) -> None:
    url = "/handoffs/journal-user"
    journal_client.patch(url + "/journal", json={"entries": [{"id": "one", "admin": "Keep this note"}]})
    assert journal_client.put(url, json={"user_key": "journal-user", "rank": "Maj"}).status_code == 200
    loaded = journal_client.get(url).json()
    assert loaded["drill_handoffs"][0]["admin"] == "Keep this note"
    assert loaded["admin_watch_items"] == ["Keep this note"]


def test_failed_handoff_replacement_preserves_previous_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = SessionHandoffStore(tmp_path)
    store.upsert(UserSessionHandoff(user_key="test-user", admin_watch_items=["Original"]))

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("Synthetic disk failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="Synthetic disk failure"):
        store.upsert(UserSessionHandoff(user_key="test-user", admin_watch_items=["Replacement"]))
    recovered = SessionHandoffStore(tmp_path).get("test-user")
    assert recovered is not None
    assert recovered.admin_watch_items == ["Original"]
    assert len(list(tmp_path.iterdir())) == 1
