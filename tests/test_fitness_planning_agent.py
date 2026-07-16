from app.services.agents.base import AgentContext
from app.services.agents.readiness_development_agents import (
    _parse_unit_pt_request,
    build_fitness_planning_agent,
)


def test_parses_count_objective_and_duration_from_plain_language() -> None:
    request, assumptions = _parse_unit_pt_request("Plan PT for 24 Marines, CFT prep, 90 minutes at the base gym")
    assert request.participant_count == 24
    assert request.objective.value == "CFT preparation"
    assert request.duration_minutes == 90
    # count/objective/duration were all supplied, so no assumption about them
    joined = " ".join(assumptions).lower()
    assert "participant count not stated" not in joined
    assert "objective not stated" not in joined
    assert "duration not stated" not in joined


def test_minutes_number_is_not_mistaken_for_participant_count() -> None:
    request, _ = _parse_unit_pt_request("45 minute mobility session for a squad of 12")
    assert request.participant_count == 12
    assert request.duration_minutes == 45
    assert request.objective.value == "mobility/recovery"


def test_hours_and_pax_phrasing() -> None:
    request, _ = _parse_unit_pt_request("strength block, 30 pax, 1 hour")
    assert request.participant_count == 30
    assert request.duration_minutes == 60
    assert request.objective.value == "strength"


def test_bare_request_uses_stated_defaults() -> None:
    request, assumptions = _parse_unit_pt_request("unit PT")
    assert request.participant_count == 20
    assert request.duration_minutes == 60
    assert request.objective.value == "general fitness"
    joined = " ".join(assumptions).lower()
    assert "assumed 20 marines" in joined
    assert "assumed 60 minutes" in joined
    assert "assumed general fitness" in joined


def test_agent_builds_a_full_plan_in_chat() -> None:
    response = build_fitness_planning_agent().run(
        "Help me plan PT for 30 Marines with an ORM matrix.", AgentContext()
    )
    answer = response.answer
    # A real scaled plan is rendered inline, not a "open the planner" pointer.
    assert "open Unit PT Planner" not in answer
    assert "Session blocks:" in answer
    assert "Staff reviews:" in answer
    assert "ORM matrix:" in answer
    assert "30 Marines" in answer
    assert response.citations  # fitness references cited
    assert "DRAFT" in answer  # advisory draft footer retained
