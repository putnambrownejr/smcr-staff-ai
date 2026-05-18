from fastapi.testclient import TestClient

from app.main import app


def _sample_request() -> dict[str, object]:
    return {
        "title": "Pre-drill company update",
        "supported_unit": "Civil affairs company",
        "supported_echelon": "company",
        "mission_or_training_goal": "Refine the next drill training plan and preserve staff continuity.",
        "timeframe": "Next 72 hours",
        "commander_priorities": [
            "Protect training value while cutting avoidable friction.",
            "Keep reporting and accountability standards tight.",
        ],
        "higher_guidance": ["Battalion expects a concise status update and decision list before final sync."],
        "met_tasks": ["Conduct mission analysis"],
        "metl_focus": ["Plan and coordinate training"],
        "section_updates": [
            {
                "section": "S-3",
                "summary": "The training concept is supportable if the company cuts to one primary lane.",
                "changes_since_last": ["A second lane was dropped after timeline review."],
                "assumptions": ["Subordinate elements can rehearse locally before drill."],
                "open_issues": ["Need final lane timeline confirmation."],
                "support_requests": ["S-4 confirms transport timeline."],
                "decisions_needed": ["Commander decides whether to keep one lane or force a second lane."],
                "risks": ["Trying to preserve two lanes will hollow out the AAR and rehearsal window."],
                "next_24_72": ["Publish refined training timeline.", "Run final planning sync."],
                "adjacent_section_asks": ["S-6 confirms report windows before final brief."],
            },
            {
                "section": "S-4",
                "summary": "Transport and water support are available, but issue/recovery timing is still tight.",
                "changes_since_last": ["One vehicle dropped from the initial estimate."],
                "assumptions": ["Issue/recovery can stay inside the same drill day."],
                "open_issues": ["Need final driver roster."],
                "support_requests": ["S-1 confirms roster and arrival windows."],
                "decisions_needed": ["XO decides whether to front-load issue the night before."],
                "risks": ["Late vehicle issue will compress movement and lane start time."],
                "next_24_72": ["Confirm drivers.", "Publish issue/recovery timeline."],
                "adjacent_section_asks": ["S-3 locks the lane start time."],
            },
        ],
        "training_only": True,
    }


def test_staff_running_estimate_builds_section_outputs() -> None:
    client = TestClient(app)

    response = client.post("/staff/running-estimate", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["running_estimates"]
    assert payload["running_estimates"][0]["section"] == "S-3"
    assert payload["command_summary"]
    assert any("advisory" in warning.lower() for warning in payload["warnings"])


def test_staff_cub_builds_command_update_brief() -> None:
    client = TestClient(app)

    response = client.post("/staff/cub", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["command_snapshot"]
    assert payload["cross_staff_friction"]
    assert payload["commander_decisions"]
    assert payload["due_outs"]
    assert payload["update_brief"]["product_type"] == "command_update_brief"


def test_staff_cpb_builds_decision_brief() -> None:
    client = TestClient(app)

    response = client.post("/staff/cpb", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["command_frame"]
    assert payload["decision_points"]
    assert payload["branches_and_sequels"]
    assert payload["command_brief"]["product_type"] == "decision_brief"


def test_staff_update_cycle_links_running_estimate_cub_and_cpb() -> None:
    client = TestClient(app)

    response = client.post("/staff/update-cycle", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["running_estimate"]["running_estimates"]
    assert payload["cub"]["update_brief"]["product_type"] == "command_update_brief"
    assert payload["cpb"]["command_brief"]["product_type"] == "decision_brief"
