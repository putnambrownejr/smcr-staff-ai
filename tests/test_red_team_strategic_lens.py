from app.services.agents.base import AgentContext
from app.services.agents.red_team_agent import build_red_team_agent


def _fictional_lens() -> dict[str, object]:
    return {
        "mode": "fictional",
        "actor_name": "Aster Guard",
        "fictional_actor_confirmed": True,
        "posture_cards": ["indirect_leverage", "information_contest"],
    }


def test_red_team_hypotheses_compares_lens_with_competing_interpretation() -> None:
    response = build_red_team_agent().run(
        "Pressure-test the exercise concept.",
        AgentContext(extra={"agent_options": {"mode": "hypotheses", "strategic_lens": _fictional_lens()}}),
    )

    assert "Strategic lens" in response.answer
    assert "Competing interpretation" in response.answer
    assert "Aster Guard" in response.answer
    assert "DRAFT — Verify all references against current official sources before acting." in response.answer


def test_red_team_assumptions_uses_lens_for_mirror_imaging_questions() -> None:
    response = build_red_team_agent().run(
        "Pressure-test the exercise concept.",
        AgentContext(extra={"agent_options": {"strategic_lens": _fictional_lens()}}),
    )

    assert "Mirror-imaging check" in response.answer
    assert "Aster Guard" in response.answer


def test_red_team_evidence_keeps_public_lens_observations_attributed() -> None:
    response = build_red_team_agent().run(
        "Pressure-test the exercise concept.",
        AgentContext(
            extra={
                "agent_options": {
                    "mode": "evidence",
                    "strategic_lens": {"mode": "public_source", "actor_name": "Example force"},
                },
                "source_evidence": [
                    {
                        "title": "Reviewed public source",
                        "excerpt": "The report describes a sustained emphasis on ambiguity.",
                        "source_hash": "reviewed-hash",
                        "trust_status": "current",
                        "url": "https://example.test/source",
                        "publisher": "Example publisher",
                        "retrieved_at": "2026-07-15",
                    }
                ],
            }
        ),
    )

    assert "Reviewed public source" in response.answer
    assert "reviewed-hash" in response.answer
    assert "Hypothesis, not fact" in response.answer
    assert any(citation.source_hash == "reviewed-hash" for citation in response.structured_citations)


def test_red_team_without_lens_preserves_existing_response_shape() -> None:
    response = build_red_team_agent().run(
        "Pressure-test the exercise concept.", AgentContext(extra={"agent_options": {"mode": "hypotheses"}})
    )

    assert "Strategic lens (exercise framing" not in response.answer
