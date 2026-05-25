from fastapi.testclient import TestClient

from app.api.routes.section_memory import get_section_memory_store
from app.api.routes.staff import get_section_memory_store as get_staff_section_memory_store
from app.main import app
from app.schemas.section_memory import SectionMemoryEntry, SectionMemoryProfileUpsertRequest
from app.services.staff.section_memory_store import SectionMemoryStore


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

    payload = _sample_request()
    payload["civil_considerations"] = ["Local community traffic near the training area."]
    payload["partner_types"] = ["Local authorities"]
    payload["coordinating_sections"] = ["G-9 Civil Affairs"]

    response = client.post("/staff/cpb", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"].startswith("Civil Preparation of the Battlespace")
    assert any("ASCOPE" in item or "Civil" in item for item in body["command_frame"])
    assert body["decision_points"]
    assert body["branches_and_sequels"]
    assert body["command_brief"]["product_type"] == "decision_brief"


def test_staff_cpb_warns_when_not_civil_affairs_relevant() -> None:
    client = TestClient(app)

    payload = _sample_request()
    payload["supported_unit"] = "Rifle company"

    response = client.post("/staff/cpb", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert any("Civil Preparation of the Battlespace" in warning for warning in body["warnings"])


def test_staff_update_cycle_links_running_estimate_cub_and_cpb() -> None:
    client = TestClient(app)

    response = client.post("/staff/update-cycle", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["running_estimate"]["running_estimates"]
    assert payload["cub"]["update_brief"]["product_type"] == "command_update_brief"
    assert payload["cpb"]["command_brief"]["product_type"] == "decision_brief"
    assert payload["cpb"]["title"].startswith("Civil Preparation")


def test_staff_mission_analysis_builds_task_and_assumption_structure() -> None:
    client = TestClient(app)

    response = client.post("/staff/mission-analysis", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["mission_statement"]
    assert payload["specified_tasks"]
    assert payload["implied_tasks"]
    assert payload["assumptions"]
    assert payload["staff_estimate_requirements"]


def test_staff_planning_cell_builds_linked_package() -> None:
    client = TestClient(app)

    response = client.post("/staff/planning-cell", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["planning_approach"]["recommended_method"] in {"mcpp", "r2p2"}
    assert payload["mission_analysis"]["mission_statement"]
    assert payload["update_cycle"]["cub"]["update_brief"]["product_type"] == "command_update_brief"
    assert payload["assumption_log"]
    assert payload["commander_decision_log"]
    assert payload["due_out_board"]


def test_staff_lone_planner_builds_thin_staff_assist_package() -> None:
    client = TestClient(app)

    response = client.post("/staff/lone-planner", json=_sample_request())

    assert response.status_code == 200
    payload = response.json()
    assert payload["posture"]
    assert payload["walk_in_brief"]
    assert payload["likely_blind_spots"]
    assert payload["missing_section_questions"]
    assert payload["cross_lane_asks"]
    assert payload["recommended_products"]
    assert payload["immediate_actions"]
    assert payload["planning_cell"]["planning_approach"]["recommended_method"] in {"mcpp", "r2p2"}


def test_staff_assisted_section_estimates_builds_gap_cover_pack() -> None:
    client = TestClient(app)

    payload = _sample_request()
    payload["focus_sections"] = ["S-1/Admin", "S-6", "XO/Chief"]
    response = client.post("/staff/assisted-section-estimates", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["posture"]
    assert body["focus_sections"] == ["S-1/Admin", "S-6", "XO/Chief"]
    assert body["section_estimates"]
    assert body["xo_walk_in_lines"]
    assert body["cross_lane_risks"]
    assert body["recommended_products"]


def test_section_memory_profile_enriches_thin_staff_outputs(tmp_path) -> None:
    store = SectionMemoryStore(tmp_path / "section-memory")
    store.upsert(
        "capt-memory",
        SectionMemoryProfileUpsertRequest(
            entries=[
                SectionMemoryEntry(
                    section="S-6",
                    title="Usual S-6 friction",
                    recurring_questions=["What access issue always slows this unit first?"],
                    recurring_failure_modes=["Reporting plan usually gets overcomplicated."],
                    preferred_checks=["Force one primary reporting method before final brief."],
                    notes=["This unit usually needs a comms simplification pass."],
                )
            ]
        ),
    )

    def override_store() -> SectionMemoryStore:
        return store

    app.dependency_overrides[get_staff_section_memory_store] = override_store
    app.dependency_overrides[get_section_memory_store] = override_store
    client = TestClient(app)
    try:
        payload = _sample_request()
        payload["user_key"] = "capt-memory"

        lone_response = client.post("/staff/lone-planner", json=payload)
        assert lone_response.status_code == 200
        lone_body = lone_response.json()
        assert any("S-6 recurring question" in item for item in lone_body["missing_section_questions"])
        assert any("S-6 preferred check" in item for item in lone_body["cross_lane_asks"])

        gap_response = client.post("/staff/assisted-section-estimates", json=payload | {"focus_sections": ["S-6"]})
        assert gap_response.status_code == 200
        gap_body = gap_response.json()
        s6 = gap_body["section_estimates"][0]
        assert "What access issue always slows this unit first?" in s6["likely_questions"]
        assert "This unit usually needs a comms simplification pass." in s6["likely_support_facts"]
    finally:
        app.dependency_overrides.clear()
