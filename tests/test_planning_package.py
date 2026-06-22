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
    assert payload["planning_approach"]["recommended_method"] in {"mcpp", "r2p2"}
    assert payload["planning_approach"]["decision"]
    assert payload["recommended_course_of_action"]
    assert any("cut" in item.lower() for item in payload["recommended_course_of_action"])
    assert payload["commander_decisions_now"]
    assert payload["top_risks"]
    assert payload["top_risks"][0].startswith("Training architecture risk:")
    assert payload["s3_plan"]["required_outputs"]
    assert payload["s4_plan"]["critical_support_requirements"]
    assert payload["s6_plan"]["pace_considerations"]
    assert [row["level"] for row in payload["s6_plan"]["pace_matrix"]] == [
        "Primary",
        "Alternate",
        "Contingency",
        "Emergency",
    ]
    assert payload["s6_plan"]["radio_guard_chart"]
    assert payload["s6_plan"]["comm_plan_outline"]
    assert payload["xo_sync"]["synchronization_matrix"]
    assert payload["command_cell"]["chief_focus_board"]
    assert payload["s1_readiness"]["routing_matrix"]
    assert payload["s1_readiness"]["admin_task_tracker"]
    assert payload["s1_readiness"]["pre_drill_admin_readiness_check"]
    assert payload["safety_plan"]["no_go_criteria"]
    assert payload["safety_plan"]["rehearsal_checks"]
    assert payload["sel_plan"]["leader_touchpoints"]
    assert payload["sel_plan"]["troop_flow_checklist"]
    assert payload["sel_plan"]["formation_transition_matrix"]
    assert payload["sel_plan"]["leader_touchpoint_plan"]
    assert payload["medical_plan"]["casevac_plan_elements"]
    assert payload["medical_plan"]["casevac_medevac_check"]
    assert payload["medical_plan"]["casualty_collection_logic"]
    assert payload["medical_plan"]["medical_decision_points"]
    assert payload["medical_plan"]["coordination_trigger_list"]
    assert payload["battalion_staff_review"]["roles_run"]
    assert payload["xo_vet"]["roles_run"] == ["xo"]
    assert payload["product_package"]
    product_types = [item["product_type"] for item in payload["product_package"]]
    assert product_types[:3] == ["warno", "frago", "aar"]
    assert "running_estimate" in product_types
    assert "synchronization_matrix" in product_types
    assert "orm_worksheet" in product_types
    assert "no_go_criteria" in product_types
    assert "residual_risk_decision_note" in product_types
    assert "rehearsal_safety_brief" in product_types
    assert "admin_estimate" in product_types
    assert "admin_task_tracker" in product_types
    assert "routing_matrix" in product_types
    assert "pre_drill_admin_readiness_check" in product_types
    assert "troop_flow_checklist" in product_types
    assert "formation_transition_matrix" in product_types
    assert "leader_touchpoint_plan" in product_types
    assert "decision_support_matrix" in product_types
    assert "due_out_tracker" in product_types
    assert "road_to_war_brief" in product_types
    assert "collection_matrix" in product_types
    assert "sustainment_matrix" in product_types
    assert "movement_table" in product_types
    assert "medical_estimate" in product_types
    assert "casevac_quick_card" in product_types
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
    product_types = [item["product_type"] for item in payload["product_package"]]
    assert product_types[:3] == ["warno", "running_estimate", "synchronization_matrix"]
    assert set(product_types[3:]) == {
        "orm_worksheet",
        "no_go_criteria",
        "residual_risk_decision_note",
        "rehearsal_safety_brief",
        "admin_estimate",
        "admin_task_tracker",
        "routing_matrix",
        "pre_drill_admin_readiness_check",
        "troop_flow_checklist",
        "formation_transition_matrix",
        "leader_touchpoint_plan",
        "decision_support_matrix",
        "due_out_tracker",
        "sustainment_matrix",
        "movement_table",
    }


def test_staff_planning_package_adds_supporting_products_without_overadding_collection_or_medical() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/staff-package",
        json={
            "title": "Staff drill synchronization package",
            "event_type": "staff_drill",
            "mission_or_training_goal": "Tighten internal staff battle rhythm and due-out discipline.",
            "coordinating_sections": ["S-1", "S-3", "S-4", "S-6"],
            "product_types": ["warno"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    product_types = [item["product_type"] for item in payload["product_package"]]
    assert product_types[:3] == ["warno", "running_estimate", "synchronization_matrix"]
    assert set(product_types[3:]) == {
        "orm_worksheet",
        "no_go_criteria",
        "residual_risk_decision_note",
        "rehearsal_safety_brief",
        "admin_estimate",
        "admin_task_tracker",
        "routing_matrix",
        "pre_drill_admin_readiness_check",
        "troop_flow_checklist",
        "formation_transition_matrix",
        "leader_touchpoint_plan",
        "decision_support_matrix",
        "due_out_tracker",
    }


def test_staff_planning_package_adds_road_to_war_brief_for_scenario_driven_request_without_s2_sources() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/staff-package",
        json={
            "title": "Littoral crisis rehearsal package",
            "event_type": "scenario_rehearsal",
            "mission_or_training_goal": (
                "Level-set a regional crisis scenario before mission analysis and staff estimates."
            ),
            "partner_types": ["Partner force"],
            "civil_considerations": ["Population displacement concerns"],
            "product_types": ["warno"],
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    product_types = [item["product_type"] for item in payload["product_package"]]
    assert "road_to_war_brief" in product_types
    assert "collection_matrix" not in product_types


def test_frago_to_conop_builds_unit_relationship_framework() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/frago-to-conop",
        json={
            "title": "Company field scenario refinement",
            "supported_echelon": "company",
            "higher_headquarters": "Battalion",
            "supported_unit": "Civil affairs company",
            "event_type": "field_training",
            "mission_or_training_goal": "Refine higher guidance into an initial company concept.",
            "raw_guidance_text": "\n".join(
                [
                    (
                        "Commander's intent: build a supportable one-day field event "
                        "that sharpens reporting and command relationships."
                    ),
                    "Task: company submits a refined FRAGO and support estimate.",
                    "Task: subordinate units provide local concept backbriefs.",
                    "Constraint: one field day only.",
                    "Coordinating instruction: report support shortfalls no later than final planning sync.",
                    "Supporting relationship: Detachment B supports reporting and observation.",
                ]
            ),
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
                {
                    "unit_name": "Detachment C",
                    "relationship": "attached",
                    "purpose": "Provide medical and accountability support",
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
    assert payload["planning_approach"]["recommended_method"] in {"mcpp", "r2p2"}
    assert payload["planning_approach"]["decision"]
    assert payload["parsed_guidance"]["directed_tasks"]
    assert payload["unit_relationship_framework"]
    assert len(payload["subordinate_conop_packets"]) == 3
    assert any("On order" in item["task_statement"] for item in payload["subordinate_conop_packets"])
    assert payload["met_alignment"]
    assert payload["frago_draft"]["product_type"] == "frago"
    assert payload["initial_conop"]["product_type"] == "conop"
    assert payload["aar_framework"]["product_type"] == "aar"
    assert payload["tdg_package"] is not None
    assert payload["tdg_package"]["forced_decision"]
    assert payload["tdg_package"]["failure_triggers"]
    assert payload["learning_cycle"]
    assert any("subordinate concept" in item.lower() for item in payload["det_follow_on_questions"])
    assert "planning_approach" in payload
    aar_prompts = str(payload["aar_framework"]["sections"])
    assert "Wargame focus:" in aar_prompts
    assert "Failure trigger to observe:" in aar_prompts


def test_frago_to_conop_runs_xo_sel_review_for_formal_event() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/frago-to-conop",
        json={
            "title": "Company change of command support package",
            "supported_echelon": "company",
            "higher_headquarters": "Battalion",
            "supported_unit": "Headquarters company",
            "event_type": "ceremony",
            "mission_or_training_goal": (
                "Support a formal public-facing ceremony with clear sequence "
                "and accountability."
            ),
            "higher_guidance": [
                "Formal event requires sequence control and clear accountability.",
                "Company publishes ceremony support FRAGO and local execution concept.",
            ],
            "formal_event": True,
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["planning_approach"]["recommended_method"] == "mcpp"
    assert payload["xo_sel_review"] is not None
    assert payload["xo_sel_review"]["roles_run"] == ["xo", "sel"]


def test_frago_to_conop_can_skip_tdg_when_requested() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/frago-to-conop",
        json={
            "title": "Internal drill sync",
            "supported_unit": "Headquarters company",
            "mission_or_training_goal": "Tighten internal reporting and support flow.",
            "include_tdg": False,
            "training_only": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "planning_approach" in payload
    assert payload["tdg_package"] is None


def test_staff_planning_package_sanitizes_sensitive_request() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/staff-package",
        json={
            "title": "Current movement plan",
            "event_type": "convoy_support",
            "mission_or_training_goal": "Update call sign RAVEN and frequency 305.5 for tonight's movement.",
            "constraints": ["Use grid coordinate 18SUJ12345678"],
            "training_only": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    flattened = str(payload)
    assert "305.5" not in flattened
    assert "RAVEN" not in flattened
    assert any("sensitive" in warning.lower() for warning in payload["warnings"])


def test_frago_to_conop_sanitizes_sensitive_request() -> None:
    client = TestClient(app)

    response = client.post(
        "/planning/frago-to-conop",
        json={
            "title": "Movement FRAGO",
            "supported_unit": "Company A",
            "mission_or_training_goal": "Update call sign RAVEN and frequency 305.5 for convoy movement.",
            "raw_guidance_text": "Grid coordinate 18SUJ12345678. NLT 2200. Use call sign RAVEN.",
            "training_only": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    flattened = str(payload)
    assert "305.5" not in flattened
    assert "RAVEN" not in flattened
    assert any("sensitive" in warning.lower() for warning in payload["warnings"])
