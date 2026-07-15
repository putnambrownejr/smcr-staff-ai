from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_cadence_routes_create_list_and_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CADENCE_STORAGE_DIR", str(tmp_path))
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/cadences/test-user",
        json={"user_key": "test-user", "title": "My Cadence", "text": "Move with purpose."},
    )
    assert response.status_code == 201
    cadence_id = response.json()["cadence_id"]

    listing = client.get("/cadences/test-user").json()
    assert any(record["cadence_id"] == cadence_id for record in listing["records"])
    assert client.delete(f"/cadences/test-user/{cadence_id}").status_code == 204
    get_settings.cache_clear()
