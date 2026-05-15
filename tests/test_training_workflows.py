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


def test_training_case_study_route_returns_s2_and_conop_implications() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/case-study",
        json={
            "title": "Urban flooding case",
            "framing_question": "What should a reserve staff learn from a public urban-disruption event?",
            "training_objective": "Sharpen planning judgment and AAR quality.",
            "audience": "Company staff",
            "source_items": [
                {
                    "title": "Official release",
                    "source_type": "official",
                    "claim": "Local flooding disrupted movement and public services.",
                    "corroborated": "true",
                }
            ],
            "met_tasks": ["Conduct mission analysis"],
            "metl_focus": ["Plan and coordinate training"],
            "constraints": ["Keep the discussion training-only"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["situation_frame"]
    assert payload["s2_estimate"]
    assert payload["met_alignment"]
    assert payload["conop_implications"]
    assert payload["aar_focus"]


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
            "primary_scenario_input": "Urban flooding disrupts movement and accountability.",
            "secondary_scenario_input": "A reporting delay and support shortfall force a branch plan.",
            "current_event_context": ["Recent heavy-rain and public-service disruption in a metro area."],
            "source_items": [
                {
                    "title": "Official weather advisory",
                    "source_type": "official",
                    "claim": "Weather disruption affects mobility and support timing.",
                    "corroborated": "true",
                }
            ],
            "met_tasks": ["Conduct mission analysis"],
            "metl_focus": ["Plan and coordinate training"],
            "constraints": ["Limited Saturday planning window"],
            "coordinating_sections": ["S-1", "S-4", "S-6"],
            "subordinate_units": [
                {
                    "unit_name": "Detachment A",
                    "relationship": "subordinate",
                    "purpose": "Run the primary lane and drive initial reporting.",
                },
                {
                    "unit_name": "Detachment B",
                    "relationship": "supporting",
                    "purpose": "Support observation and accountability tracking.",
                    "resource_bias": ["Comms", "transportation"],
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mission_analysis"]
    assert payload["scenario_frame"]
    assert payload["scenario_escalation"]
    assert payload["injects"]
    assert payload["met_alignment"]
    assert payload["coordination_matrix"]
    assert payload["battle_rhythm"]
    assert payload["required_outputs"]
    assert len(payload["subordinate_prompt_packets"]) == 2
    assert any("On order" in item["task"] for item in payload["subordinate_prompt_packets"])
    assert payload["citations"]


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
