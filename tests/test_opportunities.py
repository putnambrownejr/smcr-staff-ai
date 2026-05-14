from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.opportunities import get_tracker
from app.main import app
from app.schemas.billets import BilletUserProfile
from app.schemas.opportunities import ManualOpportunityRequest
from app.services.opportunities.tracker import OpportunityTracker


def test_opportunity_tracker_recommends_bic_and_ados_records(tmp_path: Path) -> None:
    tracker = OpportunityTracker(tmp_path)

    recommendations = tracker.recommend(
        BilletUserProfile(mos="0602", rank="Capt", desired_locations=["Austin"], keywords=["communications"]),
        [
            ManualOpportunityRequest(
                title="Communications Officer",
                opportunity_type="smcr_bic",
                unit="1/23",
                location="Austin, TX",
                mos="0602",
                rank="Capt",
                description="Open BIC with comm focus.",
            ),
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                location="Remote",
                rank="Capt",
                description="Planning support billet.",
            ),
        ],
        max_results=5,
    )

    assert recommendations
    assert recommendations[0].opportunity.title == "Communications Officer"


def test_opportunity_routes_track_and_list(tmp_path: Path) -> None:
    tracker = OpportunityTracker(tmp_path)

    def override_tracker() -> OpportunityTracker:
        return tracker

    app.dependency_overrides[get_tracker] = override_tracker
    client = TestClient(app)
    try:
        track_response = client.post(
            "/opportunities/track",
            json={
                "opportunities": [
                    {
                        "title": "ADOS Planner",
                        "opportunity_type": "ados",
                        "location": "Remote",
                        "rank": "Capt",
                        "due_date": date(2026, 6, 15).isoformat(),
                    }
                ]
            },
        )
        assert track_response.status_code == 200
        list_response = client.get("/opportunities")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert len(payload) == 1
        assert payload[0]["opportunity_type"] == "ados"
    finally:
        app.dependency_overrides.clear()
