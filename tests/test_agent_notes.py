from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.agent_notes import get_agent_notes_store
from app.core.config import get_settings
from app.main import app
from app.services.agents.notes_store import AgentNotesStore

VALID_USER_KEY = "a" * 24


@pytest.fixture()
def agent_notes_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    store = AgentNotesStore(tmp_path / "agent-notes")
    monkeypatch.setenv("LOCAL_API_KEY", "notes-secret")
    get_settings.cache_clear()
    app.dependency_overrides[get_agent_notes_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def _headers() -> dict[str, str]:
    return {"X-Local-API-Key": "notes-secret"}


def test_agent_notes_require_configured_passkey(agent_notes_client: TestClient) -> None:
    response = agent_notes_client.get(f"/agent-notes/{VALID_USER_KEY}")
    assert response.status_code == 401


def test_empty_notes_by_default(agent_notes_client: TestClient) -> None:
    response = agent_notes_client.get(f"/agent-notes/{VALID_USER_KEY}", headers=_headers())

    assert response.status_code == 200
    assert response.json() == {"agent_notes": {}, "skill_notes": {}}


def test_set_and_get_agent_note(agent_notes_client: TestClient) -> None:
    put_response = agent_notes_client.put(
        f"/agent-notes/{VALID_USER_KEY}/agent/chief-of-staff",
        headers=_headers(),
        json={"note": "Prefers terse bullet-point briefs, no filler."},
    )
    assert put_response.status_code == 200
    assert put_response.json()["agent_notes"]["chief-of-staff"] == "Prefers terse bullet-point briefs, no filler."

    get_response = agent_notes_client.get(f"/agent-notes/{VALID_USER_KEY}", headers=_headers())
    assert get_response.json()["agent_notes"]["chief-of-staff"] == "Prefers terse bullet-point briefs, no filler."


def test_set_and_get_skill_note(agent_notes_client: TestClient) -> None:
    put_response = agent_notes_client.put(
        f"/agent-notes/{VALID_USER_KEY}/skill/meeting-to-action",
        headers=_headers(),
        json={"note": "Always assign a due date, even a soft one."},
    )
    assert put_response.status_code == 200
    assert put_response.json()["skill_notes"]["meeting-to-action"] == "Always assign a due date, even a soft one."


def test_blank_note_clears_the_entry(agent_notes_client: TestClient) -> None:
    agent_notes_client.put(
        f"/agent-notes/{VALID_USER_KEY}/agent/chief-of-staff",
        headers=_headers(),
        json={"note": "temporary note"},
    )

    cleared = agent_notes_client.put(
        f"/agent-notes/{VALID_USER_KEY}/agent/chief-of-staff",
        headers=_headers(),
        json={"note": "  "},
    )

    assert cleared.status_code == 200
    assert "chief-of-staff" not in cleared.json()["agent_notes"]


def test_notes_are_isolated_per_user_key(agent_notes_client: TestClient) -> None:
    other_key = "b" * 24
    agent_notes_client.put(
        f"/agent-notes/{VALID_USER_KEY}/agent/chief-of-staff",
        headers=_headers(),
        json={"note": "user A's note"},
    )

    other_response = agent_notes_client.get(f"/agent-notes/{other_key}", headers=_headers())

    assert other_response.json()["agent_notes"] == {}
