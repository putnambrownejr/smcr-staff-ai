from app.schemas.staff import (
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
    assert "staff-battalion-s2" in ids
    assert "staff-division_group-g2" in ids


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


def test_staff_round_robin_runs_all_default_echelons() -> None:
    service = StaffCouncilService()
    response = service.round_robin(
        request=StaffRoundRobinRequest(question="Should we change the drill weekend admin battle rhythm?")
    )

    assert len(response.councils) == 3
    assert response.phases == ["initial_estimate", "critique", "cross_staff_risks", "synthesis"]


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
    assert response.support_requirements
