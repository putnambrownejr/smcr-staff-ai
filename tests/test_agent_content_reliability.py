import pytest

from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry

DEFAULT_PROMPTS: dict[str, str] = {
    # Standalone utility agents
    "chief-of-staff-aide": "Help me triage a reserve drill weekend and upcoming admin suspense.",
    "leadership-advisor": "Help me frame a PME on standards and command climate.",
    "planning-advisor": "Help me conduct deliberate MCPP for a new reserve planning problem.",
    "red-team-assumptions-challenge": "Pressure-test this plan before we brief it to the commander.",
    "assessment-learning-advisor": "Help me connect this AAR to the next drill's actual fixes.",
    "writing-briefing-coach": "Help me sharpen a command brief so the decision is clear.",
    "infantry-03xx-advisor": "Help me shape a training-safe infantry familiarization event for support Marines.",
    "artillery-08xx-advisor": "Help me shape a call-for-fire refresher drill for reserve artillery Marines.",
    "installation-practical-advisor": "Help me think through visitor access for a base event.",
    "uniform-advisor": "Help me think through the uniform and grooming prep for next drill.",
    "drill-prep-calendar": "Help me plan recurring drill reminders for next month.",
    "orm-risk-management": "Help me think through no-go criteria and residual risk for a field event.",
    "staff-products": "Build a training-only AAR draft for a field event.",
    "pki-cac-troubleshooter": "MarineNet is not prompting for my CAC certificate.",
    "osint-research-assistant": "Help me summarize public-source trends for a training scenario.",
    "terrain-map-advisor": "Help me find the right public terrain and topo references for a training area.",
    "repo-privacy-sweeper": "Review this repo before I push and look for personal data backflow.",
    # Consolidated staff archetypes
    "staff-xo": "Help me build an XO sync for the next drill weekend.",
    "staff-chief": "Help me tighten command-group continuity and due-out discipline.",
    "staff-battle_captain": "Help me shape watchboard control and escalation triggers.",
    "staff-opso": "Help me build a training plan for next drill weekend.",
    "staff-s1": "Help me organize DTS, orders, and FitRep due-outs.",
    "staff-s2": "Help me shape a public-source estimate for a training scenario.",
    "staff-s4": "Help me think through supportability for an AT movement.",
    "staff-s6": "Help me shape generic comm support for a field event.",
    "staff-sel": "Help me review a retirement ceremony and accountability sequence.",
    "staff-surgeon": "Help me think through a training-safe CASEVAC plan.",
    "staff-sja": "Issue-spot this matter before routing it further.",
    "staff-pao": "Help me think through public affairs posture for a training event.",
    "staff-safety": "Help me build a realistic ORM posture for a field event.",
    "staff-chaplain": "Help me think through a morale and welfare issue.",
    "staff-provost": "Help me think through security and access control for a base event.",
    "staff-ig": "Help me think through inspection readiness and systemic friction.",
    "staff-aviation": "Help me think through generic air-support coordination.",
    "staff-lce": "Help me think through LCE sustainment and distribution support.",
    "staff-g8": "Help me think through resource constraints and funding tradeoffs.",
    "staff-g9": "Help me think through civil considerations for a reserve event.",
}


def _prompt_for(agent_id: str) -> str:
    return DEFAULT_PROMPTS.get(agent_id, "Provide an advisory training-only staff response for this lane.")


@pytest.mark.parametrize(
    "agent_id",
    [metadata.id for metadata in AgentRegistry().list_metadata()],
)
def test_each_registered_agent_returns_a_usable_response(agent_id: str) -> None:
    registry = AgentRegistry()
    agent = registry.get(agent_id)
    assert agent is not None

    response = agent.run(
        _prompt_for(agent_id),
        context=AgentContext(request_is_training_or_fictional=True, user_role="SMCR officer"),
    )

    assert response.agent_id == agent_id
    assert response.answer.strip()
    assert response.human_review_required is True
    assert response.follow_up_questions
    assert "placeholder response" not in response.answer.lower()
    if agent.metadata.citation_required:
        assert response.structured_citations or response.source_trust


@pytest.mark.parametrize(
    "agent_id",
    [metadata.id for metadata in AgentRegistry().list_metadata()],
)
def test_each_registered_agent_degrades_safely_on_sensitive_input(agent_id: str) -> None:
    registry = AgentRegistry()
    agent = registry.get(agent_id)
    assert agent is not None

    response = agent.run(
        "Use callsign RAVEN on 305.5 MHz near grid 12345678 for this plan.",
        context=AgentContext(),
    )

    assert response.confidence == "low"
    assert any("sensitive" in warning.lower() for warning in response.warnings)
