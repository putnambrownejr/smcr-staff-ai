from app.services.agents.base import AgentContext
from app.services.agents.s3_opso_agent import build_s3_opso_agent


def test_s3_agent_distinguishes_deliberate_and_compressed_planning() -> None:
    agent = build_s3_opso_agent()

    response = agent.run(
        "Help me shape a reserve field event after late guidance changes.",
        context=AgentContext(request_is_training_or_fictional=True, user_role="SMCR officer"),
    )

    assert "Use full MCPP when the problem is new" in response.answer
    assert "Use compressed R2P2-style planning only when the mission is familiar" in response.answer
    assert any("R2P2-style refinement" in question for question in response.follow_up_questions)
