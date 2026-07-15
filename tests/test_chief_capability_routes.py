from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_chief_capability_routes_append_summary_and_undo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CADENCE_STORAGE_DIR", str(tmp_path / "cadences"))
    monkeypatch.setenv("CHIEF_CAPABILITY_AUDIT_STORAGE_DIR", str(tmp_path / "audits"))
    monkeypatch.setenv("TRAVEL_CASE_STORAGE_DIR", str(tmp_path / "travel"))
    monkeypatch.setenv("FITREP_STORAGE_DIR", str(tmp_path / "fitrep"))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/chief/capabilities",
        json={
            "user_key": "marine",
            "operation": "append_cadence",
            "payload": {"title": "Route Cadence", "text": "Move with purpose."},
        },
    )
    assert response.status_code == 200
    token = response.json()["undo_token"]
    assert client.get("/chief/capabilities/marine/summary").json()["private_cadence_count"] == 1
    undo = client.post("/chief/capabilities/undo", json={"user_key": "marine", "undo_token": token})
    assert undo.status_code == 200
    get_settings.cache_clear()
