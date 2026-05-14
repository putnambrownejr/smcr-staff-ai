from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.actions import get_tracker
from app.main import app
from app.schemas.actions import ActionItemRequest, ActionUpdateRequest
from app.services.actions.tracker import ActionTracker


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

    def override_tracker() -> ActionTracker:
        return tracker

    app.dependency_overrides[get_tracker] = override_tracker
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

        delete_response = client.delete(f"/actions/{action_id}")
        assert delete_response.status_code == 204
    finally:
        app.dependency_overrides.clear()
