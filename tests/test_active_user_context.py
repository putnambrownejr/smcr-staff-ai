from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.user_context import get_active_context_store
from app.main import app
from app.schemas.user_context import ActiveUserContext
from app.services.session.active_context_store import ActiveUserContextStore


def test_active_user_context_route_round_trip(tmp_path: Path) -> None:
    store = ActiveUserContextStore(tmp_path / "active-context")
    app.dependency_overrides[get_active_context_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.put(
            "/user-context/capt-context",
            json={
                "user_key": "capt-context",
                "unit_name": "6th Comm Battalion",
                "unit_type": "communications battalion",
                "unit_family": "SMCR comm",
                "billet_override": "CommO",
                "current_focus": ["Drill-weekend C2 rehearsal"],
                "temporary_notes": ["Treat this month like a comm battalion planning cycle."],
            },
        )
        assert response.status_code == 200
        get_response = client.get("/user-context/capt-context")
        assert get_response.status_code == 200
        payload = get_response.json()
        assert payload["unit_name"] == "6th Comm Battalion"
        assert payload["billet_override"] == "CommO"
    finally:
        app.dependency_overrides.clear()


def test_expired_active_user_context_is_not_returned(tmp_path: Path) -> None:
    store = ActiveUserContextStore(tmp_path / "active-context")
    store.upsert(
        ActiveUserContext(
            user_key="capt-expired",
            unit_name="Old Unit",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
    )

    assert store.get("capt-expired") is None
