from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.agents import get_active_context_store
from app.main import app
from app.schemas.user_context import ActiveUserContext
from app.services.session.active_context_store import ActiveUserContextStore


def test_agent_run_uses_stored_active_user_context(tmp_path: Path) -> None:
    store = ActiveUserContextStore(tmp_path / "active-context")
    store.upsert(
        ActiveUserContext(
            user_key="capt-commo",
            unit_name="6th Comm Battalion",
            unit_type="communications battalion",
            billet_override="CommO",
            current_focus=["Pre-drill PACE rehearsal"],
        )
    )
    app.dependency_overrides[get_active_context_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/agents/staff-s6/run",
            json={
                "input": "Help me think through a reserve comm plan.",
                "context": {"user_key": "capt-commo", "request_is_training_or_fictional": True},
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert "6th Comm Battalion" in payload["answer"]
        assert "CommO" in payload["answer"]
    finally:
        app.dependency_overrides.clear()
