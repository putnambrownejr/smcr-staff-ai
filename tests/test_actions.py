from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.actions import get_admin_readiness_service, get_orchestrator, get_tracker
from app.api.routes.actions import get_context_store as get_action_context_store
from app.api.routes.actions import get_update_store as get_action_update_store
from app.main import app
from app.schemas.actions import ActionItemRequest, ActionUpdateRequest
from app.schemas.session import FitrepReminder, UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.actions.tracker import ActionTracker
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore


def test_action_tracker_tracks_and_updates_records(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path)
    tracked = tracker.track(
        [
            ActionItemRequest(
                user_key="capt-action",
                title="Draft POAM",
                owner="Capt Example",
                status="open",
                priority="high",
                suspense_date=date(2026, 6, 10),
            )
        ]
    )

    assert tracked[0].title == "Draft POAM"
    updated = tracker.update(
        tracked[0].action_id,
        ActionUpdateRequest(status="in_progress", notes="Initial outline built."),
    )
    assert updated is not None
    assert updated.status.value == "in_progress"
    assert updated.history
    assert tracker.list(user_key="capt-action")


def test_action_routes_track_list_update_delete(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path)
    context_store = LocalContextStore(tmp_path / "context")
    update_store = DocumentUpdateStore(tmp_path / "updates")
    context_item = context_store.save(
        filename="orders.txt",
        content=b"Training-only orders note.",
        content_type="text/plain",
        document_type="orders",
        consent_ack=True,
    )
    update_store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="candidate-1",
                tracked_title="MCO 1610.7",
                trigger_type="maradmin",
            )
        ]
    )

    def override_tracker() -> ActionTracker:
        return tracker

    def override_context_store() -> LocalContextStore:
        return context_store

    def override_update_store() -> DocumentUpdateStore:
        return update_store

    app.dependency_overrides[get_tracker] = override_tracker
    app.dependency_overrides[get_action_context_store] = override_context_store
    app.dependency_overrides[get_action_update_store] = override_update_store
    client = TestClient(app)
    try:
        track_response = client.post(
            "/actions/track",
            json={
                "actions": [
                    {
                        "user_key": "capt-action",
                        "title": "Confirm drill POAM",
                        "owner": "Capt Example",
                        "category": "poam",
                        "priority": "high",
                        "status": "open",
                    }
                ]
            },
        )
        assert track_response.status_code == 200
        action_id = track_response.json()["tracked"][0]["action_id"]

        list_response = client.get("/actions?user_key=capt-action")
        assert list_response.status_code == 200
        assert list_response.json()[0]["title"] == "Confirm drill POAM"

        filtered_response = client.get("/actions?user_key=capt-action&owner=Capt%20Example&priority=high")
        assert filtered_response.status_code == 200
        assert len(filtered_response.json()) == 1

        update_response = client.patch(
            f"/actions/{action_id}",
            json={"status": "blocked", "notes": "Waiting on higher HQ input."},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "blocked"

        history_response = client.get(f"/actions/{action_id}/history")
        assert history_response.status_code == 200
        assert any("status: open -> blocked" in item["detail"] for item in history_response.json())

        link_response = client.post(
            f"/actions/{action_id}/links",
            json={"link_type": "local_context", "label": "Orders", "target_id": context_item.context_id},
        )
        assert link_response.status_code == 200
        assert link_response.json()["links"][0]["target_id"] == context_item.context_id

        update_link_response = client.post(
            f"/actions/{action_id}/links",
            json={"link_type": "documentation_update", "label": "PES update", "target_id": "candidate-1"},
        )
        assert update_link_response.status_code == 200
        assert len(update_link_response.json()["links"]) == 2

        remove_link_response = client.delete(
            f"/actions/{action_id}/links/{update_link_response.json()['links'][0]['link_id']}"
        )
        assert remove_link_response.status_code == 200

        delete_response = client.delete(f"/actions/{action_id}")
        assert delete_response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_action_bulk_update_route_changes_multiple_records(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path)
    tracked = tracker.track(
        [
            ActionItemRequest(user_key="capt-action", title="Item A", owner="Capt Example"),
            ActionItemRequest(user_key="capt-action", title="Item B", owner="Capt Example"),
        ]
    )

    def override_tracker() -> ActionTracker:
        return tracker

    app.dependency_overrides[get_tracker] = override_tracker
    client = TestClient(app)
    try:
        response = client.post(
            "/actions/bulk-update",
            json={
                "action_ids": [item.action_id for item in tracked],
                "status": "waiting",
                "notes": "Awaiting review.",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["updated"]) == 2
        assert all(item["status"] == "waiting" for item in payload["updated"])
    finally:
        app.dependency_overrides.clear()


def test_action_closed_status_is_supported_and_filtered_by_default(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path)
    tracked = tracker.track(
        [
            ActionItemRequest(user_key="capt-action", title="Close me", owner="Capt Example"),
        ]
    )
    updated = tracker.update(tracked[0].action_id, ActionUpdateRequest(status="closed"))

    assert updated is not None
    assert updated.status.value == "closed"
    assert tracker.list(user_key="capt-action") == []
    assert tracker.list(user_key="capt-action", include_closed=True)[0].status.value == "closed"


def test_action_promote_route_infers_category_priority_and_links(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path)
    context_store = LocalContextStore(tmp_path / "context")
    update_store = DocumentUpdateStore(tmp_path / "updates")
    context_item = context_store.save(
        filename="drill_notes.txt",
        content=b"DTS voucher due 06/10/2026. Confirm travel plan.",
        content_type="text/plain",
        document_type="other",
        consent_ack=True,
    )

    def override_tracker() -> ActionTracker:
        return tracker

    def override_context_store() -> LocalContextStore:
        return context_store

    def override_update_store() -> DocumentUpdateStore:
        return update_store

    app.dependency_overrides[get_tracker] = override_tracker
    app.dependency_overrides[get_action_context_store] = override_context_store
    app.dependency_overrides[get_action_update_store] = override_update_store
    client = TestClient(app)
    try:
        response = client.post(
            "/actions/promote",
            json={
                "user_key": "capt-action",
                "default_owner": "Capt Example",
                "source_ref": "Drill notes",
                "shared_links": [
                    {
                        "link_type": "local_context",
                        "label": "Drill notes",
                        "target_id": context_item.context_id,
                    }
                ],
                "items": [
                    {"text": "DTS voucher due 06/10/2026 after drill."},
                    {"text": "Review FitRep support form this week."},
                ],
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["tracked"]) == 2
        assert payload["tracked"][0]["category"] == "travel"
        assert payload["tracked"][0]["priority"] == "high"
        assert payload["tracked"][0]["links"]
        assert payload["tracked"][1]["category"] == "fitrep"
        assert payload["tracked"][1]["owner"] == "Capt Example"
        assert payload["summary_lines"]
    finally:
        app.dependency_overrides.clear()


def test_action_bundle_routes_track_from_chief_admin_and_at(tmp_path: Path) -> None:
    tracker = ActionTracker(tmp_path / "actions")
    context_store = LocalContextStore(tmp_path / "context")
    update_store = DocumentUpdateStore(tmp_path / "updates")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-example",
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15))],
            admin_watch_items=["DTS voucher after drill"],
        )
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "drill_plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(
            Path("C:/smcr-staff-ai/data/seed/reading_list.example.yaml")
        ),
        document_update_store=update_store,
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )
    admin_service = AdminReadinessService(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(context_store),
    )

    def override_tracker() -> ActionTracker:
        return tracker

    def override_context_store() -> LocalContextStore:
        return context_store

    def override_update_store() -> DocumentUpdateStore:
        return update_store

    def override_orchestrator() -> ChiefAideOrchestrator:
        return orchestrator

    def override_admin_service() -> AdminReadinessService:
        return admin_service

    app.dependency_overrides[get_tracker] = override_tracker
    app.dependency_overrides[get_action_context_store] = override_context_store
    app.dependency_overrides[get_action_update_store] = override_update_store
    app.dependency_overrides[get_orchestrator] = override_orchestrator
    app.dependency_overrides[get_admin_readiness_service] = override_admin_service
    client = TestClient(app)
    try:
        chief_response = client.post("/actions/from-chief-brief", json={"user_key": "capt-example"})
        assert chief_response.status_code == 200
        assert chief_response.json()["tracked"]

        admin_response = client.post("/actions/from-admin-readiness/capt-example", json={})
        assert admin_response.status_code == 200
        assert admin_response.json()["tracked"]

        at_response = client.post(
            "/actions/from-annual-training-plan",
            json={
                "plan": {
                    "unit_name": "Example Company",
                    "training_objectives": ["Run AT battle drill"],
                    "travel_required": True,
                },
                "options": {"user_key": "capt-example", "owner": "Capt Example"},
            },
        )
        assert at_response.status_code == 200
        payload = at_response.json()
        assert payload["tracked"]
        assert any(item["category"] == "training" for item in payload["tracked"])

        correspondence_response = client.post(
            "/actions/from-correspondence-conversion",
            json={
                "draft": {
                    "format_type": "naval_letter",
                    "title": "Travel support request",
                    "purpose": "Request travel support for upcoming drill attendance.",
                    "source_text": "Need a short formal request for drill travel support.",
                },
                "options": {"user_key": "capt-example", "owner": "Capt Example"},
            },
        )
        assert correspondence_response.status_code == 200
        assert correspondence_response.json()["tracked"]

        range_response = client.post(
            "/actions/from-range-package",
            json={
                "package": {
                    "event_name": "Annual rifle range",
                    "weapon_systems": ["M4"],
                    "ammunition": ["5.56 ball"],
                    "travel_required": True,
                },
                "options": {"user_key": "capt-example", "owner": "Capt Example"},
            },
        )
        assert range_response.status_code == 200
        assert range_response.json()["tracked"]

        tdg_response = client.post(
            "/actions/from-tdg",
            json={
                "tdg": {
                    "title": "Reserve convoy link-up",
                    "theme": "small-unit decision-making under time pressure",
                    "training_objective": "Practice tactical judgment.",
                },
                "options": {"user_key": "capt-example", "owner": "Capt Example"},
            },
        )
        assert tdg_response.status_code == 200
        assert tdg_response.json()["tracked"]

        poam_response = client.post(
            "/actions/from-poam",
            json={
                "poam": {
                    "title": "Drill support order POA&M",
                    "higher_guidance": [
                        "Establish reporting timeline for drill weekend support.",
                        "Coordinate S-6 comm checks and S-4 logistics support.",
                    ],
                    "staff_sections": ["S-3", "S-4", "S-6"],
                },
                "options": {"user_key": "capt-example"},
            },
        )
        assert poam_response.status_code == 200
        assert poam_response.json()["tracked"]

        tracked_actions = tracker.list(user_key="capt-example", include_closed=True)
        assert tracked_actions
        follow_up_response = client.post(
            "/actions/follow-up",
            json={
                "action_ids": [tracked_actions[0].action_id],
                "notes": "Completed after final review.",
            },
        )
        assert follow_up_response.status_code == 200
        follow_up_payload = follow_up_response.json()
        assert follow_up_payload["updated"]
        assert follow_up_payload["updated"][0]["status"] == "complete"
    finally:
        app.dependency_overrides.clear()
