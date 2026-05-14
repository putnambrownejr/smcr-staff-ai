from fastapi.testclient import TestClient

from app.main import app


def test_agent_route_preserves_unknown_context_keys_under_extra() -> None:
    client = TestClient(app)
    response = client.post(
        "/agents/osint-research-assistant/run",
        json={
            "input": "Summarize public source items.",
            "context": {
                "source_items": [
                    {
                        "title": "Official release",
                        "publisher": "Example official source",
                        "source_type": "official",
                        "url": "https://example.test/official",
                        "claim": "Public item exists.",
                        "corroborated": "true",
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    assert any("https://example.test/official" in citation for citation in response.json()["citations"])
