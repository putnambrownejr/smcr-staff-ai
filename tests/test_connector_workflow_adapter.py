from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.connectors import get_handoff_store
from app.main import app
from app.schemas.session import UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


def test_connector_workflow_adapter_returns_handoff_and_action_shapes(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    store.upsert(UserSessionHandoff(user_key="capt-adapter", admin_watch_items=["Review drill travel plan"]))

    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/connectors/workflow-adapter",
            json={
                "user_key": "capt-adapter",
                "consents": [
                    {
                        "provider": "google_calendar",
                        "access_mode": "read_only",
                        "user_key": "capt-adapter",
                        "enabled": True,
                    },
                    {
                        "provider": "gmail",
                        "access_mode": "read_only",
                        "user_key": "capt-adapter",
                        "enabled": True,
                    },
                ],
                "calendar_events": [
                    {
                        "provider": "google_calendar",
                        "title": "Drill weekend muster",
                        "start_at": "2026-06-06T08:00:00Z",
                        "location": "NOSC New Orleans",
                        "notes": "Travel the night prior.",
                    }
                ],
                "email_messages": [
                    {
                        "provider": "gmail",
                        "subject": "DTS voucher reminder",
                        "received_at": "2026-06-07T14:30:00Z",
                        "action_hint": "Voucher due this week",
                    }
                ],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["digest"]["action_items"]
        assert payload["handoff_draft_request"]["notes"]
        assert any("DTS voucher" in line for line in payload["handoff_note_lines"])
        assert payload["action_promote_request"]["items"]
        assert any(item["category"] == "admin" for item in payload["action_items"])
    finally:
        app.dependency_overrides.clear()
