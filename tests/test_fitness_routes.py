from fastapi.testclient import TestClient

from app.main import create_app


def test_fitness_route_builds_staff_reviewed_plan() -> None:
    response = TestClient(create_app()).post(
        "/fitness/unit-pt/plan",
        json={"participant_count": 30, "objective": "CFT preparation", "duration_minutes": 50},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["scaling_band"].startswith("station")
    assert any(review["role"] == "S-4" for review in payload["staff_reviews"])
    assert payload["orm"]["hazards"]
