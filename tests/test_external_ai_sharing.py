from datetime import UTC, date, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.sharing import (
    get_active_context_store,
    get_context_store,
    get_handoff_store,
    get_opportunity_tracker,
    get_plan_store,
)
from app.main import app
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.session import DrillDateRecord, FitrepReminder, PmeStatus, UserSessionHandoff
from app.schemas.user_context import ActiveUserContext
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.session.active_context_store import ActiveUserContextStore
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore


def test_external_ai_packet_redacts_sensitive_local_fields(tmp_path: Path) -> None:
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-share",
            display_name="Capt Example",
            rank="Capt",
            mos="0602",
            billet="CommO",
            rqs_context_id="ctx-rqs",
            bio_context_id="ctx-bio",
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 6, 1))],
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 30), role="MRO")],
            drill_dates=[DrillDateRecord(drill_date=date(2026, 6, 6), label="June drill")],
            admin_watch_items=["DTS voucher after drill"],
            updated_at=datetime.now(UTC),
        )
    )
    active_context_store = ActiveUserContextStore(tmp_path / "active-context")
    active_context_store.upsert(
        ActiveUserContext(
            user_key="capt-share",
            unit_name="6th Comm Battalion",
            unit_type="communications battalion",
            billet_override="CommO",
        )
    )
    context_store = LocalContextStore(tmp_path / "context")
    context_store.save(
        filename="bio.txt",
        content=b"BIO draft with phone: 555-123-4567",
        content_type="text/plain",
        document_type="bio",
    )
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    plan_store.save(
        DrillPrepPlanResponse(
            id="drill-share",
            drill_date=date(2026, 6, 6),
            tasks=[PrepTask(title="Pack gear", due_offset_days=3, due_date=date(2026, 6, 3), category="gear")],
        )
    )
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")
    opportunity_tracker.track(
        [
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                unit="4th MLG",
                source_url="https://example.test/ados",
                notes="Personal note",
            )
        ]
    )

    app.dependency_overrides[get_handoff_store] = lambda: handoff_store
    app.dependency_overrides[get_active_context_store] = lambda: active_context_store
    app.dependency_overrides[get_context_store] = lambda: context_store
    app.dependency_overrides[get_plan_store] = lambda: plan_store
    app.dependency_overrides[get_opportunity_tracker] = lambda: opportunity_tracker
    client = TestClient(app)
    try:
        response = client.post(
            "/sharing/external-ai-packet",
            json={
                "user_key": "capt-share",
                "include_document_summary": True,
                "include_drill_plans": True,
                "include_opportunities": True,
                "purpose": "a Claude planning review",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["handoff"]["mos"] == "0602"
    assert "display_name" not in payload["handoff"]
    assert payload["document_summary"]["total_documents"] == 1
    assert "records" not in payload["document_summary"]
    assert payload["drill_plans"][0]["tasks"][0]["title"] == "Pack gear"
    assert "key_events" not in payload["drill_plans"][0]
    assert "context_ids" not in payload["drill_plans"][0]
    assert payload["opportunities"][0]["title"] == "ADOS Planner"
    assert "source_url" not in payload["opportunities"][0]
    assert "handoff.display_name" in payload["redacted_fields"]
    assert payload["safe_to_share"] is False
