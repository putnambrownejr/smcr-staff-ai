from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.calendar import get_context_store, get_plan_store
from app.main import app
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.storage.local_context_store import LocalContextStore


def test_drill_plan_uses_templated_local_context_and_persists(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    context = context_store.save(
        filename="drill-template.txt",
        content=(
            b"Event: Check-in | Date: 2026-06-05 | Time: 18:00 | "
            b"Location: Reserve Center | Uniform: Service Alphas | Due: orders, CAC"
        ),
        content_type="text/plain",
        tags=["drill"],
    )
    plan_store = DrillPrepPlanStore(tmp_path / "plans")

    def override_context_store() -> LocalContextStore:
        return context_store

    def override_plan_store() -> DrillPrepPlanStore:
        return plan_store

    app.dependency_overrides[get_context_store] = override_context_store
    app.dependency_overrides[get_plan_store] = override_plan_store
    client = TestClient(app)
    try:
        response = client.post(
            "/calendar/drill-prep-plan",
            json={"drill_date": date(2026, 6, 6).isoformat(), "context_ids": [context.context_id]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["local_context_used"] is True
        assert payload["key_events"][0]["title"] == "Check-in"
        assert payload["key_events"][0]["source_context_id"] == context.context_id

        plan_id = payload["id"]
        reloaded_store = DrillPrepPlanStore(tmp_path / "plans")
        assert reloaded_store.get(plan_id) is not None
        ics_response = client.get(f"/calendar/drill-prep-plan/{plan_id}/ics")
        assert ics_response.status_code == 200
        assert "LOCATION:Reserve Center" in ics_response.text
        assert "orders\\; CAC" in ics_response.text

        get_response = client.get(f"/calendar/drill-prep-plan/{plan_id}")
        assert get_response.status_code == 200
        delete_response = client.delete(f"/calendar/drill-prep-plan/{plan_id}")
        assert delete_response.status_code == 204
        assert reloaded_store.get(plan_id) is None
    finally:
        app.dependency_overrides.clear()


def test_drill_plan_rejects_non_unclassified_key_event(tmp_path: Path) -> None:
    plan_store = DrillPrepPlanStore(tmp_path / "plans")

    def override_plan_store() -> DrillPrepPlanStore:
        return plan_store

    app.dependency_overrides[get_plan_store] = override_plan_store
    client = TestClient(app)
    try:
        response = client.post(
            "/calendar/drill-prep-plan",
            json={
                "drill_date": "2026-06-06",
                "key_events": [{"title": "Brief", "event_date": "2026-06-06", "classification_label": "CUI"}],
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
