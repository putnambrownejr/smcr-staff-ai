from app.schemas.agents import ScenarioOutputStatus
from app.services.agents.base import AgentContext
from app.services.agents.ipb_agent import build_ipb_assistant_agent
from app.services.agents.registry import AgentRegistry


def test_ipb_assistant_separates_evidence_assumptions_and_hypotheses() -> None:
    response = build_ipb_assistant_agent().run("Build an IPB scaffold.", AgentContext())

    assert "Evidence" in response.answer
    assert "Assumptions" in response.answer
    assert "Hypotheses" in response.answer
    assert response.scenario_output_status == ScenarioOutputStatus.validated
    assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")


def test_ipb_assistant_consumes_specialist_handoffs() -> None:
    response = build_ipb_assistant_agent().run(
        "Build an IPB scaffold.",
        AgentContext(
            prior_assessments={
                "area_study": {"role": "area_study", "operational_area": "Training district"},
                "actor_network": {"role": "actor_network"},
                "information_requirements": {"role": "information_requirements", "requirements": [{"indicator": "Bridge status is confirmed."}]},
            }
        ),
    )

    assert "Training district" in response.answer
    assert "Bridge status is confirmed" in response.answer


def test_ipb_assistant_is_registered() -> None:
    assert AgentRegistry().get("ipb-assistant") is not None
