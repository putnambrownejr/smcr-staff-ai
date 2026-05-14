from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.actions import get_context_store as get_action_context_store
from app.api.routes.actions import get_tracker
from app.api.routes.actions import get_update_store as get_action_update_store
from app.main import app
from app.schemas.actions import ActionItemRequest, ActionUpdateRequest
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.actions.tracker import ActionTracker
from app.services.ingestion.document_update_store import DocumentUpdateStore
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

        update_response = client.patch(
            f"/actions/{action_id}",
            json={"status": "blocked", "notes": "Waiting on higher HQ input."},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "blocked"

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
