from app.schemas.staff import StaffCouncilRequest, StaffEchelon, StaffRoundRobinRequest
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry
from app.services.staff.council import StaffCouncilService


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
