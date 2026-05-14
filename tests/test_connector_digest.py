from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.connectors import get_handoff_store
from app.main import app
from app.schemas.session import UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


def test_connector_digest_plan_builds_action_items_from_summaries(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    store.upsert(
        UserSessionHandoff(
            user_key="capt-connect",
            admin_watch_items=["DTS voucher after drill"],
        )
    )

    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/connectors/chief-digest-plan",
            json={
                "user_key": "capt-connect",
                "consents": [
                    {
                        "provider": "google_calendar",
                        "access_mode": "read_only",
                        "user_key": "capt-connect",
                        "enabled": False,
                    },
                    {
                        "provider": "gmail",
                        "access_mode": "read_only",
                        "user_key": "capt-connect",
                        "enabled": False,
                    },
                ],
                "calendar_events": [
                    {
                        "provider": "google_calendar",
                        "title": "Drill weekend muster",
                        "start_at": "2026-06-06T08:00:00Z",
                        "location": "NOSC New Orleans",
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
        assert payload["summary_lines"]
        assert payload["read_plans"]
        assert any(item["category"] == "calendar" for item in payload["action_items"])
        assert any(item["category"] == "email" for item in payload["action_items"])
        assert payload["staged_write_actions"]
    finally:
        app.dependency_overrides.clear()
