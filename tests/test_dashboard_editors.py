from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_editor_state_is_protected_and_persistent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SMCR_STAFF_AI_HOME", str(tmp_path))
    monkeypatch.setenv("LOCAL_API_KEY", "editor-test")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        endpoint = "/dashboard/editors/synthetic-editor"
        assert client.get(endpoint).status_code == 401
        headers = {"X-Local-API-Key": "editor-test"}
        assert client.get(endpoint, headers=headers).status_code == 404
        payload = {"staffLaneNotes": {"S1": "Keep this note"}, "gearItems": [{"id": 1, "name": "Notebook"}], "staffLaneContacts": {"S1": [{"id": 2, "name": "Synthetic contact"}]}}
        assert client.put(endpoint, headers=headers, json=payload).status_code == 200
        saved = client.get(endpoint, headers=headers).json()
        for key, value in payload.items():
            assert saved[key] == value
        assert client.get("/dashboard/editors/another-user", headers=headers).status_code == 404
        assert client.put(endpoint, headers=headers, json={"unknown": "not accepted"}).status_code == 422
        assert client.get(endpoint, headers=headers).json() == saved
    finally:
        get_settings.cache_clear()
