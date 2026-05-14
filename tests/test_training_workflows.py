from fastapi.testclient import TestClient

from app.main import app


def test_training_scenario_builder_returns_admin_and_orm_requirements() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            "scenario_type": "staff_drill",
            "title": "Battalion planning drill",
            "training_objective": "Practice decision-making and product flow.",
            "constraints": ["Three-hour window"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["admin_requirements"]
    assert payload["orm_considerations"]
    assert payload["aar_prompts"]


def test_range_safety_builder_returns_roles_and_controls() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/range-safety",
        json={
            "event_name": "Annual rifle range",
            "weapon_systems": ["M4"],
            "ammunition": ["5.56 ball"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "RSO" in payload["required_roles"]
    assert payload["orm_controls"]
