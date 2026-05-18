import pytest

from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry

PROTOTYPE_AGENT_IDS = {"mos-commo", "mos-civil-affairs"}

DEFAULT_PROMPTS: dict[str, str] = {
    "chief-of-staff-aide": "Help me triage a reserve drill weekend and upcoming admin suspense.",
    "s1-admin-chief": "Help me organize DTS, orders, and FitRep due-outs.",
    "s2-intel": "Help me shape a public-source estimate for a training scenario.",
    "s3-opso": "Help me build a training plan for next drill weekend.",
    "s4-logistics": "Help me think through supportability for an AT movement.",
    "s6-comms": "Help me shape generic comm support for a field event.",
    "sel-enlisted-leader": "Help me review a retirement ceremony and accountability sequence.",
    "medical-doc-advisor": "Help me think through a training-safe CASEVAC plan.",
    "g9-civil-military": "Help me think through civil considerations for a reserve event.",
    "airo-advisor": "Help me think through generic air-support coordination.",
    "jag-legal-advisor": "Issue-spot this matter before routing it further.",
    "chaplain-advisor": "Help me think through a morale and welfare issue.",
    "leadership-advisor": "Help me frame a PME on standards and command climate.",
    "mcpp-planning-assistant": "Help me conduct deliberate MCPP for a new reserve planning problem.",
    "opt-facilitator": "Help me run mission analysis with an OPT that keeps drifting.",
    "red-team-assumptions-challenge": "Pressure-test this plan before we brief it to the commander.",
    "assessment-learning-advisor": "Help me connect this AAR to the next drill's actual fixes.",
    "writing-briefing-coach": "Help me sharpen a command brief so the decision is clear.",
    "joint-interagency-frame-advisor": "Help me think through command relationships and outside stakeholders.",
    "installation-practical-advisor": "Help me think through visitor access for a base event.",
    "maradmin-monitor": "Help me triage a new MARADMIN for reserve staff relevance.",
    "uniform-advisor": "Help me think through the uniform and grooming prep for next drill.",
    "drill-prep-calendar": "Help me plan recurring drill reminders for next month.",
    "doctrine-opord-assistant": "Help me turn higher guidance into a cleaner FRAGO and CONOP draft.",
    "training-planner": "Help me shape a training event that can actually be assessed.",
    "orm-risk-management": "Help me think through no-go criteria and residual risk for a field event.",
    "staff-products": "Build a training-only AAR draft for a field event.",
    "admin-readiness-advisor": "Help me review general admin readiness before drill.",
    "pki-cac-troubleshooter": "MarineNet is not prompting for my CAC certificate.",
    "correspondence-formatting": "Give me a naval letter formatting checklist.",
    "fitrep-assistant": "Help me organize FitRep support inputs and suspense items.",
    "osint-research-assistant": "Help me summarize public-source trends for a training scenario.",
    "terrain-map-advisor": "Help me find the right public terrain and topo references for a training area.",
    "r2p2-planning-assistant": "Help me conduct compressed R2P2-style refinement for a familiar event.",
    "repo-privacy-sweeper": "Review this repo before I push and look for personal data backflow.",
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
    if agent_id not in PROTOTYPE_AGENT_IDS:
        assert "placeholder response" not in response.answer.lower()
    if agent.metadata.citation_required and agent_id not in PROTOTYPE_AGENT_IDS:
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
