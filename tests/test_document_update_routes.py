from fastapi.testclient import TestClient

from app.main import app


def test_document_update_check_route_returns_candidates() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/check-updates",
        json=[
            {
                "source_id": "maradmin-123-26",
                "title": "MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
                "canonical_url": "https://example.test/maradmin-123-26",
                "summary": "This message announces an update to FitRep/PES policy published on MCPEL.",
                "tags": ["DocumentUpdate"],
                "source_hash": "abc123",
            }
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidates"]
    assert payload["candidates"][0]["human_review_required"] is True
