from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.handoffs import get_handoff_store
from app.main import app
from app.schemas.session import UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


def test_handoff_draft_update_extracts_patch(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)

    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/handoffs/capt-draft/draft-update",
            json={
                "notes": (
                    "- PME: EWSDEP incomplete due 2026-06-30\n"
                    "- FitRep Annual for MRO due 06/15/2026\n"
                    "- DTS voucher after drill\n"
                    "- Every drill confirm uniform and haircut\n"
                    "- Trend: interested in broadening assignment\n"
                    "- MarineNet course: writing refresher\n"
                    "- Read: MCDP 1 Warfighting\n"
                    "- Preference: location = New Orleans"
                )
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["confirmation_required"] is True
        assert payload["patch"]["pme"][0]["program"] == "EWSDEP"
        assert payload["patch"]["fitreps"][0]["occasion"] == "Annual"
        assert "DTS voucher after drill" in payload["patch"]["admin_watch_items"]
        assert "Every drill confirm uniform and haircut" in payload["patch"]["recurring_drill_notes"]
        assert payload["patch"]["recommended_courses"]
        assert payload["patch"]["recommended_books"]
        assert payload["patch"]["preferences"]["location"] == "New Orleans"
    finally:
        app.dependency_overrides.clear()


def test_handoff_apply_update_merges_confirmed_patch(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    store.upsert(UserSessionHandoff(user_key="capt-apply", admin_watch_items=["Existing admin note"]))

    app.dependency_overrides[get_handoff_store] = lambda: store
    client = TestClient(app)
    try:
        response = client.post(
            "/handoffs/capt-apply/apply-update",
            json={
                "patch": {
                    "pme": [{"program": "EWSDEP", "status": "incomplete", "due_date": "2026-06-30"}],
                    "fitreps": [{"occasion": "Annual", "due_date": "2026-06-15", "role": "MRO"}],
                    "admin_watch_items": ["DTS voucher after drill"],
                    "recommended_courses": ["MarineNet writing refresher"],
                }
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert "pme" in payload["applied_categories"]
        assert any(item["program"] == "EWSDEP" for item in payload["handoff"]["pme"])
        assert "Existing admin note" in payload["handoff"]["admin_watch_items"]
        assert "DTS voucher after drill" in payload["handoff"]["admin_watch_items"]
    finally:
        app.dependency_overrides.clear()
