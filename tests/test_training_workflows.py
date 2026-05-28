from fastapi.testclient import TestClient

from app.main import app


def test_training_scenario_preset_catalog_lists_first_pass_presets() -> None:
    client = TestClient(app)

    response = client.get("/training/scenario-presets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_presets"] >= 4
    ids = {item["preset_id"] for item in payload["records"]}
    assert "baltic-littoral-coercion" in ids
    assert "hadr-armed-opportunists" in ids


def test_training_scenario_builder_returns_admin_and_orm_requirements() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            "scenario_type": "staff_drill",
            "title": "Battalion planning drill",
            "training_objective": "Practice decision-making and product flow.",
            "scenario_archetype": "littoral_hybrid",
            "inject_tags": ["comms_degraded", "media_pressure"],
            "primary_scenario_input": (
                "A partner force in a fictional coastal city requests support as access degrades."
            ),
            "secondary_scenario_input": (
                "A hostile proxy group exploits port congestion and rumor to delay movement."
            ),
            "current_event_context": [
                "Use real-world-style littoral instability without copying a live conflict."
            ],
            "coordinating_sections": ["S-3", "S-4", "S-6", "Medical"],
            "constraints": ["Three-hour window"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["admin_requirements"]
    assert payload["orm_considerations"]
    assert payload["aar_prompts"]
    assert payload["scenario_setting"]
    assert payload["adversary_profile"]
    assert payload["threat_actor_stereotypes"]
    assert payload["inject_matrix"]
    assert payload["facilitator_notes"]
    assert payload["redcell_questions"]
    assert payload["scenario_archetype_used"] == "littoral_hybrid"
    assert payload["inject_tags_used"] == ["comms_degraded", "media_pressure"]
    assert "fictional" in payload["scenario_setting"][0].lower()
    assert payload["adversary_profile"][0]["name"]
    assert any(item["title"] == "Comms blackout window" for item in payload["inject_matrix"])
    assert payload["threat_actor_stereotypes"][0]["preferred_seams"]


def test_training_scenario_builder_applies_preset_defaults() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            "scenario_type": "staff_drill",
            "title": "Preset-driven planning drill",
            "training_objective": "Stress command decisions with a ready-made scenario package.",
            "scenario_preset_id": "baltic-littoral-coercion",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_archetype_used"] == "littoral_hybrid"
    assert payload["inject_tags_used"] == ["comms_degraded", "media_pressure", "partner_force_failure"]
    assert any("corridor" in item.lower() for item in payload["scenario_setting"])


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
    assert payload["no_go_criteria"]
    assert payload["leader_verification_questions"]


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
    assert payload["no_go_criteria"]
    assert payload["command_decision_points"]
    assert payload["medevac_and_comm_checks"]


def test_s3_planner_returns_battle_rhythm_and_outputs() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/s3-plan",
        json={
            "title": "Battalion drill planning sync",
            "mission_or_training_goal": "Align staff outputs and support requirements for next drill weekend.",
            "event_type": "drill_weekend",
            "scenario_archetype": "disaster_unrest",
            "inject_tags": ["casualty", "logistics_failure", "disinformation"],
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
    assert payload["scenario_archetype_used"] == "disaster_unrest"
    assert payload["inject_tags_used"] == ["casualty", "logistics_failure", "disinformation"]
    assert payload["scenario_setting"]
    assert payload["scenario_frame"]
    assert payload["adversary_profile"]
    assert payload["threat_actor_stereotypes"]
    assert payload["scenario_escalation"]
    assert payload["narrative_beats"]
    assert payload["injects"]
    assert payload["inject_matrix"]
    assert payload["facilitator_notes"]
    assert payload["redcell_questions"]
    assert payload["adversary_profile"][0]["signature_tactics"]
    assert any("Phase II" in item["phase"] or "Phase III" in item["phase"] for item in payload["inject_matrix"])
    assert any(item["title"] == "Casualty inject" for item in payload["inject_matrix"])
    assert any(item["title"] == "Support collapse" for item in payload["inject_matrix"])
    assert payload["threat_actor_stereotypes"][0]["likely_friendly_mistakes"]
    assert payload["met_alignment"]
    assert payload["coordination_matrix"]
    assert payload["battle_rhythm"]
    assert payload["required_outputs"]
    assert len(payload["subordinate_prompt_packets"]) == 2
    assert any("On order" in item["task"] for item in payload["subordinate_prompt_packets"])
    assert payload["citations"]


def test_s3_planner_applies_scenario_preset_defaults() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/s3-plan",
        json={
            "title": "Preset-driven S-3 scenario drill",
            "mission_or_training_goal": "Use a ready scenario package to test staff synchronization.",
            "scenario_preset_id": "urban-unrest-partner-fragility",
            "event_type": "staff_drill",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_archetype_used"] == "urban_unrest"
    assert payload["inject_tags_used"] == ["civil_unrest", "disinformation", "legal_gray_zone"]
    assert any(item["title"] == "Legal ambiguity" for item in payload["inject_matrix"])


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


def test_tdg_builder_returns_decision_forcing_wargame_package() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/tdg",
        json={
            "title": "Reserve convoy link-up",
            "theme": "decision-making under time pressure",
            "audience": "company-grade officers and SNCOs",
            "training_objective": "Force an early decision, branch plan, and reserve-realistic risk tradeoff.",
            "scenario_context": ["Two elements are trying to link up after weather disrupts movement."],
            "opposing_factors": ["Reporting is delayed and route confidence is low."],
            "friendly_forces": ["One element is late and communications are degraded."],
            "reserve_friction": ["Compressed drill timeline", "Un-rehearsed handoff"],
            "decision_time": "10 minutes",
            "references": ["MCDP 1 Warfighting"],
            "constraints": ["45-minute session"],
            "include_red_team": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "TDG / wargaming package" in payload["title"]
    assert payload["commander_problem"]
    assert payload["forced_decision"]
    assert payload["decision_points"]
    assert payload["no_regret_actions"]
    assert payload["branch_sequel_prompts"]
    assert payload["failure_triggers"]
    assert payload["red_team_points"]
    assert payload["aar_focus"]


def test_infantry_training_package_returns_modified_urban_familiarization_structure() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/infantry-package",
        json={
            "title": "AT MOUT familiarization",
            "training_goal": "Take logistics and admin Marines through a modified urban familiarization package.",
            "unit_name": "Example logistics detachment",
            "audience": "AT support Marines",
            "primary_training_population": "logistics and admin Marines",
            "venue_type": "MOUT town",
            "ammunition_type": "blank ammunition",
            "training_window": "one AT training day",
            "constraints": ["Keep the package basic and supervised."],
            "support_requirements": ["Qualified safety oversight", "Medical support", "Blank-fire SOP"],
            "met_tasks": ["Conduct rehearsals", "Maintain accountability"],
            "metl_focus": ["Basic warfighting familiarization"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "03 familiarization package" in payload["title"]
    assert payload["training_frame"]
    assert payload["recommended_scope"]
    assert payload["training_phases"]
    assert payload["lane_design"]
    assert payload["blank_fire_controls"]
    assert payload["evaluation_points"]
    assert any("Urban Operations" in item for item in payload["citations"])
