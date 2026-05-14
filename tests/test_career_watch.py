from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.career import get_career_watch_service
from app.main import app
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.session import CareerTrend, FitrepReminder, PmeStatus, UserSessionHandoff
from app.services.career.watch import CareerWatchService
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore


def test_career_watch_route_surfaces_core_signals(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")

    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-career",
            rank="Capt",
            mos="0602",
            updated_at=datetime.now(UTC) - timedelta(days=35),
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 6, 1))],
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15), role="MRO")],
            recommended_courses=["MarineNet writing refresher"],
            career_trends=[
                CareerTrend(
                    label="Broadening assignment interest",
                    recommended_action="Review ADOS and reserve billet options this month.",
                )
            ],
        )
    )
    context_store.save(
        filename="bio.txt",
        content=b"Professional bio draft",
        content_type="text/plain",
        tags=["career"],
        document_type="bio",
        consent_ack=True,
    )
    opportunity_tracker.track(
        [
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                unit="4th MLG",
                location="New Orleans, LA",
                due_date=date(2026, 6, 20),
            )
        ]
    )

    def override_service() -> CareerWatchService:
        return CareerWatchService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            opportunity_tracker=opportunity_tracker,
            reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        )

    app.dependency_overrides[get_career_watch_service] = override_service
    client = TestClient(app)
    try:
        response = client.get("/career/watch/capt-career")
        assert response.status_code == 200
        payload = response.json()
        assert payload["handoff_is_stale"] is True
        titles = [item["title"] for item in payload["watch_items"]]
        assert any("PME watch: EWSDEP" in title for title in titles)
        assert any("Opportunity watch: ADOS Planner" in title for title in titles)
        assert "MarineNet writing refresher" in payload["recommended_courses"]
    finally:
        app.dependency_overrides.clear()


def test_career_watch_response_without_handoff_still_guides_setup(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")

    def override_service() -> CareerWatchService:
        return CareerWatchService(
            handoff_store=SessionHandoffStore(tmp_path / "handoffs"),
            document_organizer=PersonalDocumentOrganizer(context_store),
            opportunity_tracker=opportunity_tracker,
            reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        )

    app.dependency_overrides[get_career_watch_service] = override_service
    client = TestClient(app)
    try:
        response = client.get("/career/watch/new-user")
        assert response.status_code == 200
        payload = response.json()
        assert payload["handoff"] is None
        assert payload["watch_items"][0]["title"] == "Create session handoff for career tracking"
    finally:
        app.dependency_overrides.clear()
