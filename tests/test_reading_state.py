from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.reading_state import get_reading_state_store
from app.main import app
from app.services.reading.state_store import ReadingProgressStore


def test_reading_progress_round_trip(tmp_path: Path) -> None:
    app.dependency_overrides[get_reading_state_store] = lambda: ReadingProgressStore(tmp_path / "reading-state")
    client = TestClient(app)
    try:
        update = client.put(
            "/reading-list/state/capt-reader/warfighting",
            json={
                "status": "in_progress",
                "notes": ["Strong refresher on friction.", "Useful PME tie-in for reserve staff judgment."],
            },
        )

        assert update.status_code == 200
        payload = update.json()
        assert payload["slug"] == "warfighting"
        assert payload["status"] == "in_progress"

        listed = client.get("/reading-list/state/capt-reader")

        assert listed.status_code == 200
        list_payload = listed.json()
        assert list_payload["user_key"] == "capt-reader"
        assert any(record["slug"] == "warfighting" for record in list_payload["records"])
    finally:
        app.dependency_overrides.clear()
