from app.schemas.agents import ScenarioOutputStatus
from app.services.agents.base import AgentContext
from app.services.agents.information_requirements_agent import build_information_requirements_agent
from app.services.agents.registry import AgentRegistry


def test_information_manager_links_each_requirement_to_a_decision() -> None:
    response = build_information_requirements_agent().run("What must the commander know before a route decision?", AgentContext())

    assert response.scenario_output is not None
    requirements = response.scenario_output["requirements"]
    assert requirements
    assert all(item["decision_supported"] for item in requirements)
    assert response.scenario_output_status == ScenarioOutputStatus.validated


def test_information_manager_consumes_prior_assessments_and_local_evidence() -> None:
    response = build_information_requirements_agent().run(
        "Prepare a decision register.",
        AgentContext(
            prior_assessments={"area_study": {"role": "area_study"}, "actor_network": {"role": "actor_network"}},
            extra={"source_evidence": [{"title": "Scenario note", "source_hash": "irm-hash", "chunk_id": "source:1", "excerpt": "Access depends on a public coordination process.", "trust_status": "current"}]},
        ),
    )

    assert any(citation.source_hash == "irm-hash" for citation in response.structured_citations)
    assert "Area study: received" in response.answer
    assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")


def test_information_requirements_manager_is_registered() -> None:
    assert AgentRegistry().get("information-requirements-manager") is not None
