from fastapi.testclient import TestClient

from app.main import app


def test_staff_planning_package_builds_cross_staff_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/staff-package",
        json={
            "title": "Reserve field training package",
            "event_type": "field_training",
            "mission_or_training_goal": "Build a one-day field event that improves staff and small-unit readiness.",
            "audience": "Civil affairs company",
            "timeframe": "Next drill weekend",
            "constraints": ["One field day", "Distributed Marines", "Travel required"],
            "coordinating_sections": ["S-1", "S-4", "S-6", "Safety / ORM"],
            "support_requirements": ["Billeting", "Movement accountability", "Medical support"],
            "partner_types": ["Community partner"],
            "civil_considerations": ["Limited local familiarity between drills"],
            "medical_risk_context": ["Heat injury risk"],
            "casualty_scenarios": ["Vehicle rollover"],
            "source_items": [
                {
                    "title": "Official release",
                    "source_type": "official",
                    "claim": "Local public context requires coordination.",
                    "corroborated": "true",
                }
            ],
            "product_types": ["warno", "frago", "aar"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_course_of_action"]
    assert any("cut" in item.lower() for item in payload["recommended_course_of_action"])
    assert payload["commander_decisions_now"]
    assert payload["top_risks"]
    assert payload["top_risks"][0].startswith("Training architecture risk:")
    assert payload["s3_plan"]["required_outputs"]
    assert payload["s4_plan"]["critical_support_requirements"]
    assert payload["s6_plan"]["pace_considerations"]
    assert payload["medical_plan"]["casevac_plan_elements"]
    assert payload["battalion_staff_review"]["roles_run"]
    assert payload["xo_vet"]["roles_run"] == ["xo"]
    assert payload["product_package"]
    assert payload["g9_plan"] is not None


def test_staff_planning_package_skips_g9_when_not_relevant() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/staff-package",
        json={
            "title": "Drill synchronization package",
            "event_type": "drill_weekend",
            "mission_or_training_goal": "Tighten internal staff coordination for the next drill.",
            "constraints": ["Short planning window"],
            "support_requirements": ["Equipment issue"],
            "product_types": ["warno"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["g9_plan"] is None
    assert payload["general_staff_review"] is None


def test_frago_to_conop_builds_unit_relationship_framework() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/frago-to-conop",
        json={
            "title": "Company field scenario refinement",
            "higher_headquarters": "Battalion",
            "supported_unit": "Civil affairs company",
            "event_type": "field_training",
            "mission_or_training_goal": "Refine higher guidance into an initial company concept.",
            "higher_guidance": [
                "Battalion FRAGO directs one-day field event.",
                "Company will provide a subordinate concept and support estimate.",
            ],
            "s3_inputs": ["Need MET/METL alignment and subordinate task clarity."],
            "g9_inputs": ["Civil considerations should remain generic and training-only."],
            "subordinate_units": [
                {
                    "unit_name": "Detachment A",
                    "relationship": "subordinate",
                    "purpose": "Run the primary field lane",
                    "planning_requirements": ["Refine local movement plan"],
                },
                {
                    "unit_name": "Detachment B",
                    "relationship": "supporting",
                    "purpose": "Support reporting and observation",
                },
            ],
            "met_tasks": ["Conduct mission analysis"],
            "metl_focus": ["Plan and coordinate training"],
            "constraints": ["One field day", "Distributed Marines"],
            "support_requirements": ["Transportation", "Medical support"],
            "coordinating_sections": ["S-1", "S-4", "S-6", "Medical"],
            "product_types": ["frago", "aar"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["unit_relationship_framework"]
    assert payload["met_alignment"]
    assert payload["frago_draft"]["product_type"] == "frago"
    assert payload["initial_conop"]["product_type"] == "conop"
    assert payload["aar_framework"]["product_type"] == "aar"
    assert any("subordinate concept" in item.lower() for item in payload["det_follow_on_questions"])
