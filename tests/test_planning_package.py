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
