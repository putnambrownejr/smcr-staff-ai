from app.services.agents.base import AgentContext
from app.services.agents.s2_intel_agent import build_s2_intel_agent


def test_s2_intel_agent_calls_for_source_tiering() -> None:
    agent = build_s2_intel_agent()

    response = agent.run(
        "Help me frame a public-source estimate for a training scenario in the Baltics.",
        AgentContext(request_is_training_or_fictional=True, user_role="S-2"),
    )

    assert "Tier sources explicitly" in response.answer
    assert "CIA World Factbook" in response.answer
    assert any("official current-source lane" in question for question in response.follow_up_questions)
    assert any("Tier:" in (citation.notes or "") for citation in response.structured_citations)
