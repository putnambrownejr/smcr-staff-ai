from datetime import date, timedelta

_FUTURE_DRILL = date.today() + timedelta(days=21)
from pathlib import Path  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.api.routes.calendar import get_context_store, get_handoff_store, get_plan_store  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.session import DrillDateRecord, RecurringCheck, UserSessionHandoff  # noqa: E402
from app.services.calendar.plan_store import DrillPrepPlanStore  # noqa: E402
from app.services.session.handoff_store import SessionHandoffStore  # noqa: E402
from app.services.storage.local_context_store import LocalContextStore  # noqa: E402


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
            json={"drill_date": _FUTURE_DRILL.isoformat(), "context_ids": [context.context_id]},
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
                "drill_date": _FUTURE_DRILL.isoformat(),
                "key_events": [
                    {
                        "title": "Brief",
                        "event_date": _FUTURE_DRILL.isoformat(),
                        "classification_label": "CUI",
                    }
                ],
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_handoff_reminder_plan_route_generates_plans_from_stored_rhythm(tmp_path: Path) -> None:
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-rhythm",
            unit_id="example-unit",
            drill_dates=[DrillDateRecord(drill_date=_FUTURE_DRILL, label="June drill")],
            recurring_drill_notes=["Every drill confirm uniform and haircut."],
            recurring_checks=[
                RecurringCheck(
                    title="After drill review DTS voucher and close travel-admin loose ends.",
                    cadence="post_drill",
                    category="travel",
                    due_offset_days=3,
                )
            ],
        )
    )

    def override_plan_store() -> DrillPrepPlanStore:
        return plan_store

    def override_handoff_store() -> SessionHandoffStore:
        return handoff_store

    app.dependency_overrides[get_plan_store] = override_plan_store
    app.dependency_overrides[get_handoff_store] = override_handoff_store
    client = TestClient(app)
    try:
        response = client.post("/calendar/handoffs/capt-rhythm/reminder-plans", json={})
        assert response.status_code == 200
        payload = response.json()
        assert payload["generated_plan_ids"]
        assert payload["plans"]
        task_titles = {task["title"] for task in payload["plans"][0]["tasks"]}
        assert "Every drill confirm uniform and haircut." in task_titles
        assert "After drill review DTS voucher and close travel-admin loose ends." in task_titles
    finally:
        app.dependency_overrides.clear()
