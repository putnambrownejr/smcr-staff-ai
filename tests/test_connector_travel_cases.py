from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.connectors import get_handoff_store
from app.main import app
from app.schemas.session import UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


def test_connector_workflow_adapter_extracts_travel_case_details(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    store.upsert(UserSessionHandoff(user_key="capt-travel"))

    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/connectors/workflow-adapter",
            json={
                "user_key": "capt-travel",
                "consents": [
                    {
                        "provider": "gmail",
                        "access_mode": "read_only",
                        "user_key": "capt-travel",
                        "enabled": True,
                    }
                ],
                "email_messages": [
                    {
                        "provider": "gmail",
                        "subject": "CI Travel itinerary and rental car confirmation",
                        "sender": "noreply@citravel.example",
                        "received_at": "2026-06-01T14:30:00Z",
                        "action_hint": "Travel scheduled 06/06/2026 to 06/08/2026.",
                        "notes": "Rental car reserved. Collect receipts after return.",
                        "body_preview": "Depart 06/06/2026 return 06/08/2026. Rental car pickup confirmed.",
                    }
                ],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["travel_cases"]
        case = payload["travel_cases"][0]
        assert case["travel_start"] == "2026-06-06"
        assert case["travel_end"] == "2026-06-08"
        assert case["voucher_due_date"] == "2026-06-13"
        assert case["rental_car_expected"] is True
        assert "rental car" in {item.lower() for item in case["receipts_to_collect"]}
        assert any("voucher due" in line.lower() for line in payload["handoff_note_lines"])
        assert any(item["category"] == "travel" for item in payload["action_items"])
    finally:
        app.dependency_overrides.clear()
