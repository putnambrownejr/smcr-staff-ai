import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.agents.base import AgentContext
from app.services.agents.red_team_agent import build_red_team_agent


@pytest.mark.parametrize(
    ("mode", "heading"),
    [
        ("assumptions", "What to challenge"),
        ("evidence", "Claim ledger"),
        ("hypotheses", "Competing hypotheses"),
    ],
)
def test_red_team_modes_are_distinct_and_include_draft_warning(mode: str, heading: str) -> None:
    response = build_red_team_agent().run(
        "Test this planning claim.",
        AgentContext(extra={"agent_options": {"mode": mode}}),
    )

    assert heading in response.answer
    assert "DRAFT — Verify all references against current official sources before acting." in response.answer


def test_red_team_evidence_mode_uses_local_evidence_as_the_claim_ledger() -> None:
    response = build_red_team_agent().run(
        "Test this planning claim.",
        AgentContext(
            extra={
                "agent_options": {"mode": "evidence"},
                "source_evidence": [
                    {
                        "title": "Approved bridge survey",
                        "excerpt": "The bridge is restricted to light vehicles until inspection is complete.",
                        "source_hash": "abc123",
                        "chunk_id": "chunk-1",
                    }
                ],
            }
        ),
    )

    assert "Approved bridge survey" in response.answer
    assert "light vehicles" in response.answer
    assert any(citation.source_hash == "abc123" for citation in response.structured_citations)


def test_red_team_evidence_mode_without_sources_marks_collection_need() -> None:
    response = build_red_team_agent().run(
        "Test this planning claim.",
        AgentContext(extra={"agent_options": {"mode": "evidence"}}),
    )

    assert "Collection need" in response.answer


def test_red_team_route_rejects_unsupported_mode() -> None:
    client = TestClient(app)

    response = client.post(
        "/agents/red-team-assumptions-challenge/run",
        json={"input": "Test this planning claim.", "options": {"mode": "unsupported"}},
    )

    assert response.status_code == 422
    assert "Unsupported Red Team mode" in response.json()["detail"]


def test_red_team_route_passes_options_into_agent_context() -> None:
    client = TestClient(app)

    response = client.post(
        "/agents/red-team-assumptions-challenge/run",
        json={"input": "Test this planning claim.", "options": {"mode": "evidence"}},
    )

    assert response.status_code == 200
    assert "Claim ledger" in response.json()["answer"]
