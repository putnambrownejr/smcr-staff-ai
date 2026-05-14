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


def test_annual_training_planner_returns_admin_and_logistics_checks() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/annual-training-plan",
        json={
            "unit_name": "Example Company",
            "training_objectives": ["Complete AT readiness lane", "Run staff battle drill"],
            "date_window": "FY26 Q3",
            "travel_required": True,
            "distributed_personnel": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["planning_phases"]
    assert payload["admin_due_outs"]
    assert payload["logistics_considerations"]
    assert payload["coordination_points"]


def test_range_package_planner_returns_packet_and_safety_elements() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/range-package",
        json={
            "event_name": "Annual rifle range",
            "unit_name": "Example Company",
            "weapon_systems": ["M4"],
            "ammunition": ["5.56 ball"],
            "travel_required": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["packet_components"]
    assert payload["roles_and_responsibilities"]
    assert payload["medevac_and_comm_checks"]


def test_s3_planner_returns_battle_rhythm_and_outputs() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/s3-plan",
        json={
            "title": "Battalion drill planning sync",
            "mission_or_training_goal": "Align staff outputs and support requirements for next drill weekend.",
            "event_type": "drill_weekend",
            "constraints": ["Limited Saturday planning window"],
            "coordinating_sections": ["S-1", "S-4", "S-6"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mission_analysis"]
    assert payload["coordination_matrix"]
    assert payload["battle_rhythm"]
    assert payload["required_outputs"]


def test_s4_planner_returns_support_and_sustainment_elements() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/s4-plan",
        json={
            "title": "AT logistics sync",
            "supported_event": "Annual training movement",
            "support_objective": "Support distributed personnel arrival and sustainment.",
            "travel_required": True,
            "overnight": True,
            "support_requirements": ["Billeting", "Chow", "Equipment issue"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["support_estimate"]
    assert payload["critical_support_requirements"]
    assert payload["movement_and_billeting"]
    assert payload["sustainment_checks"]
