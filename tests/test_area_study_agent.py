from app.schemas.agents import ScenarioOutputStatus
from app.services.agents.area_study_agent import build_area_study_agent
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


def test_area_study_builder_labels_unsupplied_facts_as_gaps() -> None:
    response = build_area_study_agent().run("Build an area study for a training scenario.", AgentContext())

    assert "Evidence gaps" in response.answer
    assert response.scenario_output_status == ScenarioOutputStatus.validated
    assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")
    assert response.scenario_output is not None
    assert response.scenario_output["role"] == "area_study"


def test_area_study_builder_cites_resolved_local_evidence() -> None:
    context = AgentContext(
        extra={
            "source_evidence": [
                {
                    "title": "Training infrastructure note",
                    "publisher": "Scenario control",
                    "url": "https://example.test/training-note",
                    "retrieved_at": "2026-07-15T00:00:00+00:00",
                    "source_hash": "abc123",
                    "chunk_id": "source-1:0",
                    "excerpt": "The exercise bridge is closed for maintenance.",
                    "trust_status": "current",
                }
            ]
        }
    )
    response = build_area_study_agent().run("Assess the area.", context)

    assert any(citation.source_hash == "abc123" for citation in response.structured_citations)
    assert "exercise bridge is closed" in response.answer


def test_area_study_builder_is_registered() -> None:
    assert AgentRegistry().get("area-study-builder") is not None
