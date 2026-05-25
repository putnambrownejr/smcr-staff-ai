from fastapi.testclient import TestClient

from app.main import app
from app.schemas.staff import (
    MagtfLens,
    S2EstimateRequest,
    S6PlanRequest,
    StaffCouncilRequest,
    StaffEchelon,
    StaffRoundRobinRequest,
)
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry
from app.services.staff.council import StaffCouncilService
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner


def test_registry_includes_chief_and_staff_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert "chief-of-staff-aide" in ids
    assert "staff-company-xo" in ids
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
    assert "staff-mef-ace" in ids
    assert "staff-mef-lce" in ids
    assert "staff-hqmc-hqmc_mra" in ids
    assert "staff-hqmc-hqmc_ppo" in ids
    assert "staff-hqmc-hqmc_aviation" in ids


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

    assert len(response.councils) == 20
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
    assert StaffEchelon.mef in echelons_run
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
    assert payload["nine_line_considerations"]
    assert payload["casevac_plan_elements"]


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
