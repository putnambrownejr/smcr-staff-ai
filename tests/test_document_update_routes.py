from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

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


def test_document_update_routes_persist_and_update_status(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    from app.services.ingestion.document_update_store import DocumentUpdateStore
    from app.services.ingestion.source_state_store import SourceStateStore

    store = DocumentUpdateStore(tmp_path)
    state_store = SourceStateStore(tmp_path / "states")
    monkeypatch.setattr("app.api.routes.documents._update_store", store)
    monkeypatch.setattr("app.api.routes.documents._source_state_store", state_store)
    client = TestClient(app)

    create_response = client.post(
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
    assert create_response.status_code == 200
    candidate_id = create_response.json()["candidates"][0]["candidate_id"]

    list_response = client.get("/documents/updates")
    assert list_response.status_code == 200
    assert list_response.json()

    status_response = client.post(
        f"/documents/updates/{candidate_id}/status",
        json={"review_status": "reviewed", "review_notes": "Verified against official page."},
    )
    assert status_response.status_code == 200
    assert status_response.json()["review_status"] == "reviewed"

    filtered_response = client.get("/documents/updates?status=reviewed")
    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1

    accept_response = client.post(
        f"/documents/source-states/accept/{candidate_id}",
        json={
            "status": "current",
            "current_version": "2026.1",
            "verification_source_url": "https://example.test/official-current",
            "notes": "Verified current against official source.",
        },
    )
    assert accept_response.status_code == 200
    accept_payload = accept_response.json()
    assert accept_payload["status"] == "current"
    assert accept_payload["accepted_candidate_id"] == candidate_id

    states_response = client.get("/documents/source-states")
    assert states_response.status_code == 200
    assert len(states_response.json()) == 1

    accepted_filter = client.get("/documents/updates?status=accepted")
    assert accepted_filter.status_code == 200
    assert len(accepted_filter.json()) == 1
