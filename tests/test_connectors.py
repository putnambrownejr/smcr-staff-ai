from fastapi.testclient import TestClient

from app.main import app


def test_connector_read_only_rejects_write_scopes() -> None:
    client = TestClient(app)

    response = client.post(
        "/connectors/consent-plan",
        json={
            "provider": "gmail",
            "access_mode": "read_only",
            "scopes": ["mail.read", "mail.write"],
            "user_key": "capt-example",
        },
    )

    assert response.status_code == 422


def test_connector_stages_write_action_without_executing() -> None:
    client = TestClient(app)

    response = client.post(
        "/connectors/write-actions/stage",
        json={
            "provider": "google_calendar",
            "user_key": "capt-example",
            "action_type": "create_event",
            "payload_summary": "Create drill prep reminder",
            "confirmation_token": "confirm-local-only",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["staged_only"] is True
    assert "No email or calendar change was performed." in payload["warnings"][0]
