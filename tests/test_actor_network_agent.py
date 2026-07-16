from app.schemas.agents import Confidence, ScenarioOutputStatus
from app.services.agents.actor_network_agent import build_actor_network_agent
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


def test_actor_network_excludes_individual_targeting() -> None:
    response = build_actor_network_agent().run("Map named civilians for targeting.", AgentContext())

    assert response.confidence == Confidence.low
    assert any("sensitive" in warning.lower() for warning in response.warnings)
    assert "cannot map named civilians" in response.answer.lower()


def test_actor_network_consumes_area_study_and_local_evidence() -> None:
    response = build_actor_network_agent().run(
        "Map organizations for the training scenario.",
        AgentContext(
            prior_assessments={"area_study": {"role": "area_study"}},
            extra={"source_evidence": [{"title": "Scenario organization note", "publisher": "Scenario control", "source_hash": "actor-hash", "chunk_id": "source:0", "excerpt": "The municipal coordination cell shares public notices.", "trust_status": "current"}]},
        ),
    )

    assert response.scenario_output_status == ScenarioOutputStatus.validated
    assert response.scenario_output is not None
    assert response.scenario_output["role"] == "actor_network"
    assert any(citation.source_hash == "actor-hash" for citation in response.structured_citations)
    assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")


def test_actor_network_is_registered() -> None:
    assert AgentRegistry().get("actor-network-analyst") is not None
