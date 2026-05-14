from datetime import UTC, date, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.chief import get_orchestrator
from app.main import app
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.session import PmeStatus, UserSessionHandoff
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore


def test_get_chief_brief_route_returns_sorted_actions(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-route",
            updated_at=datetime.now(UTC),
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 5, 20))],
        )
    )
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    plan_store.save(
        DrillPrepPlanResponse(
            id="drill-route",
            drill_date=date(2026, 6, 6),
            tasks=[
                PrepTask(
                    title="Pack gear",
                    due_offset_days=3,
                    due_date=date(2026, 6, 3),
                    category="gear",
                )
            ],
        )
    )

    def override_orchestrator() -> ChiefAideOrchestrator:
        return ChiefAideOrchestrator(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            drill_plan_store=plan_store,
            reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        )

    app.dependency_overrides[get_orchestrator] = override_orchestrator
    client = TestClient(app)
    try:
        response = client.get("/chief/brief/capt-route")
        assert response.status_code == 200
        payload = response.json()
        assert payload["user_key"] == "capt-route"
        assert payload["action_items"]
        priorities = [item["priority"] for item in payload["action_items"]]
        assert priorities == sorted(priorities, key=lambda priority: {"high": 0, "medium": 1, "low": 2}[priority])
    finally:
        app.dependency_overrides.clear()
