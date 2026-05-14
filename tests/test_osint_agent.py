from app.services.agents.base import AgentContext
from app.services.agents.osint_agent import build_osint_agent


def test_osint_agent_requires_citations_and_counterarguments() -> None:
    agent = build_osint_agent()
    context = AgentContext(
        extra={
            "source_items": [
                {
                    "title": "Official update",
                    "publisher": "Example official source",
                    "source_type": "official",
                    "url": "https://example.test/official",
                    "claim": "The public event date changed.",
                    "counterargument": "The update may not apply to all subordinate activities.",
                    "corroborated": "true",
                    "retrieved_at": "2026-05-13T00:00:00Z",
                },
                {
                    "title": "Local reporting",
                    "publisher": "Example news",
                    "source_type": "news",
                    "url": "https://example.test/news",
                    "summary": "Local reporting repeats the date change.",
                    "corroborated": "true",
                },
            ]
        }
    )

    response = agent.run("Aggregate public discussion around a training event date change.", context)

    assert response.citations
    assert any("https://example.test/official" in citation for citation in response.citations)
    assert "Counterarguments and alternative explanations" in response.answer
    assert "Truth" in response.answer or "Assessment:" in response.answer
    assert response.human_review_required is True


def test_osint_agent_no_sources_stays_low_confidence() -> None:
    agent = build_osint_agent()
    response = agent.run("What is the public trend?", AgentContext())

    assert response.confidence == "low"
    assert response.citations == ["No source URLs supplied; no factual claims are verified."]
    assert "No trusted public source items supplied" in response.answer
