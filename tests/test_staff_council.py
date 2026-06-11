from fastapi.testclient import TestClient

from app.main import app
from app.schemas.staff import (
    CommandCellRequest,
    MagtfLens,
    S1ReadinessRequest,
    S2EstimateRequest,
    S6PlanRequest,
    SafetyPlanningRequest,
    SelExecutionRequest,
    StaffCouncilRequest,
    StaffEchelon,
    StaffRoundRobinRequest,
    XoSyncRequest,
)
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry
from app.services.staff.command_cell_planner import CommandCellPlanner
from app.services.staff.council import StaffCouncilService
from app.services.staff.s1_readiness_planner import S1ReadinessPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff.safety_planner import SafetyPlanner
from app.services.staff.sel_execution_planner import SelExecutionPlanner
from app.services.staff.xo_sync_planner import XoSyncPlanner


def test_registry_includes_chief_and_staff_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert "chief-of-staff-aide" in ids
    assert "staff-company-xo" in ids
    assert "staff-battalion-chief" in ids
    assert "staff-battalion-battle_captain" in ids
    assert "staff-company-doc" in ids
    assert "staff-company-safety" in ids
    assert "staff-battalion-s2" in ids
    assert "staff-battalion-surgeon" in ids
    assert "staff-battalion-sja" in ids
    assert "staff-battalion-pao" in ids
    assert "staff-battalion-safety" in ids
    assert "staff-regiment_meu_wing-airo" in ids
    assert "staff-regiment_meu_wing-sja" in ids
    assert "staff-regiment_meu_wing-ace" in ids
    assert "staff-regiment_meu_wing-lce" in ids
    assert "staff-division_group-g2" in ids
    assert "staff-division_group-g7" in ids
    assert "staff-division_group-g8" in ids
    assert "staff-division_group-g9" in ids
    assert "staff-division_group-wing_ops" in ids
    assert "staff-division_group-mlg_log" in ids
    assert "staff-division_group-surgeon" in ids
    # MEF and HQMC echelons were intentionally removed — division_group is the
    # top supported echelon for an SMCR-focused tool.
    assert not any(id_.startswith("staff-mef-") for id_ in ids)
    assert not any(id_.startswith("staff-hqmc-") for id_ in ids)


def test_chief_of_staff_agent_surfaces_handoff_watch_items() -> None:
    registry = AgentRegistry()
    agent = registry.get("chief-of-staff-aide")
    assert agent is not None

    response = agent.run(
        "Build my weekly staff triage.",
        AgentContext(
            extra={
                "handoff": {
                    "pme": ["EWSDEP incomplete"],
                    "fitreps": ["RS closeout due next month"],
                    "admin_watch_items": ["DTS voucher follow-up"],
                }
            }
        ),
    )

    assert "EWSDEP incomplete" in response.answer
    assert "RS closeout due next month" in response.answer
    assert "DTS voucher follow-up" in response.answer


def test_staff_council_battalion_s2_uses_osint_tie_in() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="Should we adjust our public affairs posture for a training event?",
            echelon=StaffEchelon.battalion,
            roles=["s2"],
            context={
                "source_items": [
                    {
                        "title": "Official release",
                        "publisher": "Example official source",
                        "source_type": "official",
                        "url": "https://example.test/official",
                        "claim": "Training event details were publicly announced.",
                        "corroborated": "true",
                    }
                ]
            },
        )
    )

    assert len(response.perspectives) == 1
    assert response.perspectives[0].role == "s2"
    assert response.perspectives[0].citations
    assert "OSINT" in response.perspectives[0].answer
    assert response.perspectives[0].structured_citations


def test_staff_round_robin_runs_all_default_echelons() -> None:
    service = StaffCouncilService()
    response = service.round_robin(
        request=StaffRoundRobinRequest(question="Should we change the drill weekend admin battle rhythm?")
    )

    # 4 default echelons (company → division_group) × 4 phases = 16
    assert len(response.councils) == 16
    assert response.phases == [
        "section_estimates",
        "critique_other_sections",
        "cross_staff_friction",
        "commander_xo_synthesis",
    ]
    assert {perspective.phase for council in response.councils for perspective in council.perspectives} == set(
        response.phases
    )
    division_group_council = next(
        council for council in response.councils if council.echelon == StaffEchelon.division_group
    )
    assert "g9" not in division_group_council.roles_run


def test_staff_council_firstsgt_uses_sel_grounding() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="How should we tighten accountability and ceremony sequence for a formal company event?",
            echelon=StaffEchelon.company,
            roles=["firstsgt"],
        )
    )

    assert len(response.perspectives) == 1
    assert response.perspectives[0].role == "firstsgt"
    assert "sequence control" in response.perspectives[0].answer
    assert response.perspectives[0].structured_citations


def test_staff_round_robin_includes_g9_when_relevant() -> None:
    service = StaffCouncilService()
    response = service.round_robin(
        request=StaffRoundRobinRequest(
            question="How should we coordinate with community partners for a humanitarian support exercise?"
        )
    )

    division_group_council = next(
        council for council in response.councils if council.echelon == StaffEchelon.division_group
    )
    assert "g9" in division_group_council.roles_run
    assert "staff fight" in response.synthesis


def test_staff_council_rejects_unknown_role() -> None:
    service = StaffCouncilService()

    try:
        service.vet_idea(
            StaffCouncilRequest(
                question="Test",
                echelon=StaffEchelon.company,
                roles=["space-ops"],
            )
        )
    except ValueError as exc:
        assert "Unknown roles" in str(exc)
    else:
        raise AssertionError("Expected invalid role to raise ValueError")


def test_staff_council_special_staff_builds_exercise_products() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question=(
                "Build a realistic MEU exercise plan with aviation support, media presence, safety risk, "
                "and legal review."
            ),
            echelon=StaffEchelon.regiment_meu_wing,
            roles=["AirO", "SJA", "PAO", "safety", "provost", "chaplain"],
        )
    )

    roles = {perspective.role for perspective in response.perspectives}
    assert roles == {"airo", "sja", "pao", "safety", "provost", "chaplain"}
    airo = next(perspective for perspective in response.perspectives if perspective.role == "airo")
    sja = next(perspective for perspective in response.perspectives if perspective.role == "sja")

    assert MagtfLens.ace in airo.magtf_lenses
    assert "Air support estimate" in airo.recommended_products
    assert any("airspace" in item.lower() for item in airo.critical_questions)
    assert any("qualified aviation" in item.lower() for item in airo.assumptions_to_test)
    assert "Legal estimate" in sja.recommended_products
    assert any("not legal advice" in item.lower() for item in sja.assumptions_to_test)
    assert all(perspective.structured_citations for perspective in response.perspectives)
    assert any(
        citation.get("title") == "MCWP 5-10 Marine Corps Planning Process"
        for perspective in response.perspectives
        for citation in perspective.structured_citations
    )


def test_staff_council_special_staff_aliases() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="Check public release and legal guardrails for a training exercise.",
            echelon=StaffEchelon.regiment_meu_wing,
            roles=["JAG", "public affairs", "provost marshal"],
        )
    )

    assert [perspective.role for perspective in response.perspectives] == ["sja", "pao", "provost"]


def test_staff_council_pao_and_provost_recommend_new_products() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="Build a battalion training event with guest access, media interest, and tight site control.",
            echelon=StaffEchelon.battalion,
            roles=["pao", "provost"],
        )
    )

    pao = next(perspective for perspective in response.perspectives if perspective.role == "pao")
    provost = next(perspective for perspective in response.perspectives if perspective.role == "provost")

    assert "Public affairs plan" in pao.recommended_products
    assert "response-to-query lines" in pao.recommended_products
    assert "Security annex" in provost.recommended_products
    assert "visitor control checklist" in provost.recommended_products


def test_staff_council_g8_and_ig_recommend_new_products() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question=(
                "Pressure-test a reserve event with constrained support dollars and recurring "
                "inspection friction."
            ),
            echelon=StaffEchelon.division_group,
            roles=["g8", "ig"],
        )
    )

    g8 = next(perspective for perspective in response.perspectives if perspective.role == "g8")
    ig = next(perspective for perspective in response.perspectives if perspective.role == "ig")

    assert "resource estimate" in [item.lower() for item in g8.recommended_products]
    assert "resourcing decision point" in [item.lower() for item in g8.recommended_products]
    assert "inspection readiness plan" in [item.lower() for item in ig.recommended_products]
    assert "readiness trend memo" in [item.lower() for item in ig.recommended_products]


def test_staff_round_robin_runs_airo_sja_where_available() -> None:
    service = StaffCouncilService()
    response = service.round_robin(
        StaffRoundRobinRequest(
            question="Pressure-test a high-level MAGTF exercise with aviation and legal review.",
            roles=["airo", "sja"],
        )
    )

    roles_run = {role for council in response.councils for role in council.roles_run}
    echelons_run = {council.echelon for council in response.councils}
    assert {"airo", "sja"}.issubset(roles_run)
    assert StaffEchelon.regiment_meu_wing in echelons_run
    assert StaffEchelon.division_group in echelons_run
    assert all(council.roles_missing == [] for council in response.councils)


def test_staff_council_route_serializes_special_staff_fields() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/vet-idea",
        json={
            "question": "Build an exercise plan with aviation support and legal review.",
            "echelon": "regiment_meu_wing",
            "roles": ["airo", "sja"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["roles_run"] == ["airo", "sja"]
    assert payload["perspectives"][0]["recommended_products"]
    assert payload["perspectives"][0]["magtf_lenses"]
    assert payload["perspectives"][0]["mcpp_step"]


def test_staff_council_staff_product_references_follow_numbered_staff() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="Build the base OPORD and running estimate requirements for a battalion exercise.",
            echelon=StaffEchelon.battalion,
            roles=["s3", "s4", "s6"],
        )
    )

    assert all(
        any(
            citation.get("title") == "MCWP 5-10 Marine Corps Planning Process"
            for citation in perspective.structured_citations
        )
        for perspective in response.perspectives
    )

    xo = service.vet_idea(
        StaffCouncilRequest(
            question="Tighten staff synchronization for a battalion field exercise.",
            echelon=StaffEchelon.battalion,
            roles=["xo"],
        )
    )
    assert "XO sync matrix" in xo.perspectives[0].recommended_products

    s1 = service.vet_idea(
        StaffCouncilRequest(
            question="Clean up admin readiness and routing for next drill.",
            echelon=StaffEchelon.battalion,
            roles=["s1"],
        )
    )
    assert "admin estimate" in s1.perspectives[0].recommended_products
    assert "admin task tracker" in s1.perspectives[0].recommended_products
    assert "pre-drill admin readiness check" in s1.perspectives[0].recommended_products

    safety = service.vet_idea(
        StaffCouncilRequest(
            question="Build a realistic ORM posture for a field event with convoy movement and overnight sustainment.",
            echelon=StaffEchelon.battalion,
            roles=["safety"],
        )
    )
    assert "ORM worksheet" in safety.perspectives[0].recommended_products
    assert "residual-risk decision note" in safety.perspectives[0].recommended_products

    sgtmaj = service.vet_idea(
        StaffCouncilRequest(
            question="Tighten accountability and standards for a formal battalion event.",
            echelon=StaffEchelon.battalion,
            roles=["sgtmaj"],
        )
    )
    assert "troop-flow checklist" in sgtmaj.perspectives[0].recommended_products
    assert "formation/transition matrix" in sgtmaj.perspectives[0].recommended_products


def test_s2_estimator_returns_claims_and_gaps() -> None:
    service = S2Estimator()
    response = service.build(
        request=S2EstimateRequest(
            title="Exercise sentiment estimate",
            question="What does public reporting suggest about upcoming exercise sentiment?",
            source_items=[
                {
                    "title": "Official release",
                    "source_type": "official",
                    "claim": "The event is proceeding as planned.",
                    "corroborated": "true",
                }
            ],
        )
    )

    assert response.summary_assessment
    assert response.assessed_claims
    assert response.collection_gaps


def test_s6_planner_returns_pace_and_support_requirements() -> None:
    service = S6Planner()
    response = service.build(
        request=S6PlanRequest(
            title="Drill comm sync",
            supported_event="Drill weekend planning event",
            c2_objective="Support leader coordination and accountability.",
            support_requirements=["Equipment issue", "Battery plan"],
        )
    )

    assert response.c2_support_estimate
    assert response.pace_considerations
    assert [row["level"] for row in response.pace_matrix] == ["Primary", "Alternate", "Contingency", "Emergency"]
    assert all("failure_trigger" in row for row in response.pace_matrix)
    assert response.radio_guard_chart
    assert any("Pre-execution" in row["period"] for row in response.radio_guard_chart)
    assert any("PACE matrix" in item for item in response.comm_plan_outline)
    assert any("Radio guard" in item for item in response.comm_plan_outline)
    assert any("real frequencies" in item for item in response.information_management_checks)
    assert response.support_requirements


def test_xo_sync_planner_returns_sync_and_due_out_products() -> None:
    service = XoSyncPlanner()
    response = service.build(
        XoSyncRequest(
            title="Battalion drill sync",
            supported_event="drill weekend",
            command_focus="Protect the training standard and tighten staff handoffs.",
            coordinating_sections=["S-1", "S-3", "S-4", "S-6"],
            critical_decisions=["Cut one lane to protect quality."],
            due_outs=["Publish support suspense list."],
        )
    )

    assert response.command_sync_frame
    assert response.synchronization_matrix
    assert response.decision_support_matrix
    assert response.due_out_tracker


def test_command_cell_planner_returns_chief_and_battle_captain_outputs() -> None:
    service = CommandCellPlanner()
    response = service.build(
        CommandCellRequest(
            title="Battalion command cell prep",
            supported_event="drill weekend",
            command_focus="Protect the commander's picture and clean handoffs.",
            coordinating_sections=["S-3", "S-4", "S-6"],
            critical_decisions=["Cut one lane to preserve execution quality."],
            due_outs=["Publish final support suspense tracker."],
        )
    )

    assert response.command_cell_frame
    assert response.chief_focus_board
    assert response.battle_captain_watchboard
    assert response.command_update_lines
    assert response.turnover_handoff_notes
    assert response.ccir_and_decision_triggers


def test_s1_readiness_planner_returns_admin_products() -> None:
    service = S1ReadinessPlanner()
    response = service.build(
        S1ReadinessRequest(
            title="Next drill admin prep",
            supported_event="drill weekend",
            admin_priorities=["Roster scrub", "DTS suspense"],
            admin_risks=["Late routing"],
        )
    )

    assert response.readiness_estimate
    assert response.admin_status_board
    assert response.admin_task_tracker
    assert response.routing_matrix
    assert response.pre_drill_admin_readiness_check
    assert response.critical_suspenses


def test_safety_planner_returns_orm_and_no_go_structure() -> None:
    service = SafetyPlanner()
    response = service.build(
        SafetyPlanningRequest(
            title="Field event risk review",
            supported_event="field exercise",
            hazards=["Heat injury"],
            live_fire=True,
            vehicle_ops=True,
        )
    )

    assert response.orm_framework
    assert response.no_go_criteria
    assert response.residual_risk_decisions
    assert response.rehearsal_checks
    assert response.stop_training_triggers


def test_sel_execution_planner_returns_accountability_and_standards_outputs() -> None:
    service = SelExecutionPlanner()
    response = service.build(
        SelExecutionRequest(
            title="Company formal event",
            supported_event="change of command rehearsal",
            accountability_risks=["Sequence confusion"],
            formal_event=True,
        )
    )

    assert response.troop_flow_plan
    assert response.troop_flow_checklist
    assert response.accountability_scheme
    assert response.formation_transition_matrix
    assert response.leader_touchpoints
    assert response.leader_touchpoint_plan
    assert response.standards_checks
    assert response.marine_welfare_checks


def test_g9_planner_returns_partner_and_continuity_elements() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/g9-plan",
        json={
            "title": "Community coordination support",
            "supported_problem": "Prepare for a training event with local community touchpoints.",
            "partner_types": ["Local authorities", "Community partners"],
            "civil_considerations": ["Limited local familiarity between drills"],
            "constraints": ["Keep everything public-source and advisory"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["civil_situation_frame"]
    assert payload["partner_coordination"]
    assert payload["continuity_and_transition"]


def test_staff_routes_return_xo_s1_safety_and_sel_outputs() -> None:
    client = TestClient(app)

    xo_response = client.post(
        "/staff/xo-sync",
        json={
            "title": "Battalion sync",
            "supported_event": "drill weekend",
            "command_focus": "Resolve the first real friction point and assign owners.",
        },
    )
    assert xo_response.status_code == 200
    assert xo_response.json()["synchronization_matrix"]

    command_cell_response = client.post(
        "/staff/command-cell",
        json={
            "title": "Command cell prep",
            "supported_event": "drill weekend",
            "command_focus": "Keep the commander's picture current and assign owners.",
        },
    )
    assert command_cell_response.status_code == 200
    assert command_cell_response.json()["chief_focus_board"]

    s1_response = client.post(
        "/staff/s1-readiness",
        json={
            "title": "S-1 prep",
            "supported_event": "drill weekend",
            "admin_priorities": ["Roster scrub"],
        },
    )
    assert s1_response.status_code == 200
    assert s1_response.json()["routing_matrix"]

    safety_response = client.post(
        "/staff/safety-plan",
        json={
            "title": "Safety prep",
            "supported_event": "field exercise",
            "hazards": ["Heat injury"],
        },
    )
    assert safety_response.status_code == 200
    assert safety_response.json()["no_go_criteria"]

    sel_response = client.post(
        "/staff/sel-execution",
        json={
            "title": "SEL prep",
            "supported_event": "drill weekend",
            "accountability_risks": ["Late accountability"],
        },
    )
    assert sel_response.status_code == 200
    assert sel_response.json()["leader_touchpoints"]


def test_medical_planner_returns_tccc_and_casevac_elements() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/medical-plan",
        json={
            "title": "Field event med plan",
            "supported_event": "One-day field event",
            "medical_risk_context": ["Heat injury risk"],
            "casualty_scenarios": ["Vehicle rollover"],
            "travel_required": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["medical_support_estimate"]
    assert payload["tccc_considerations"]
    assert payload["tccc_knowledge_points"]
    assert payload["nine_line_considerations"]
    assert payload["casevac_plan_elements"]
    assert payload["casevac_medevac_check"]
    assert payload["casualty_collection_logic"]
    assert payload["medical_decision_points"]
    assert payload["medical_rehearsal_checks"]
    assert payload["coordination_trigger_list"]


def test_staff_council_normalizes_doc_alias() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="How should we think about casualty response for a field event?",
            echelon=StaffEchelon.company,
            roles=["corpsman"],
        )
    )

    assert len(response.perspectives) == 1
    assert response.perspectives[0].role == "doc"


def test_staff_council_synthesis_pushes_to_resolve_friction() -> None:
    service = StaffCouncilService()
    response = service.vet_idea(
        StaffCouncilRequest(
            question="Should we run a one-day field event with distributed Marines and limited vehicles?",
            echelon=StaffEchelon.battalion,
            roles=["s3", "s4", "s6"],
        )
    )

    assert "executable plan" in response.synthesis
    assert "Best immediate move" in response.synthesis


def test_staff_s6_pki_wrapper_route_returns_pki_playbook() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s6/pki-troubleshooting",
        json={
            "title": "Portal access issue",
            "issue_type": "portal_access_issue",
            "symptoms": ["Portal loads but access fails after CAC selection."],
            "affected_systems": ["Marine Online"],
            "on_government_furnished_equipment": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["issue_type"] == "portal_access_issue"
    assert payload["immediate_checks"]


def test_staff_s2_osint_wrapper_route_runs_specialist_lane() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s2/osint-estimate",
        json={
            "input": "Build a public-source estimate for the commander.",
            "context": {
                "source_items": [
                    {
                        "title": "Official release",
                        "publisher": "Example official source",
                        "source_type": "official",
                        "url": "https://example.test/official",
                        "claim": "Training event details were publicly announced.",
                        "corroborated": "true",
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_id"] == "osint-research-assistant"
    assert payload["citations"]
    assert "counterarguments" in payload["answer"].lower()


def test_staff_s1_dts_helper_route_returns_s1_travel_admin_workflow() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s1/dts-helper",
        json={
            "title": "Next drill authorization",
            "facts": ["Travel starts Friday night."],
            "constraints": ["Need approval before Thursday."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "dts_authorization"
    assert payload["required_documents"]


def test_staff_s1_gtcc_helper_route_returns_s1_gtcc_workflow() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff/s1/gtcc-helper",
        json={
            "title": "Travel card follow-up",
            "facts": ["Voucher is pending."],
            "constraints": ["Avoid delinquency risk."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_type"] == "gtcc"
    assert any("gtcc" in item.lower() or "travel-card" in item.lower() for item in payload["checklist"])
