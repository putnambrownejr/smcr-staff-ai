from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes.documents import get_source_state_store as get_document_source_state_store
from app.api.routes.documents import get_update_store as get_document_update_store
from app.api.routes.source_updates import get_update_store as get_source_update_store
from app.core.config import get_settings
from app.main import app
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.ingestion.document_update_store import DocumentUpdateStore

API_KEY = "test-local-key"


def test_document_and_source_update_routes_require_api_key_when_configured(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", API_KEY)
    get_settings.cache_clear()
    client = TestClient(app)
    try:
        checks = [
            client.post("/documents/check-updates", json=[]),
            client.get("/documents/updates"),
            client.post(
                "/documents/updates/missing/status",
                json={"review_status": "reviewed", "trust_state": "verified_current"},
            ),
            client.post(
                "/documents/source-states/accept/missing",
                json={"status": "current", "current_version": "2026.1"},
            ),
            client.get("/source-updates"),
            client.post("/source-updates/missing/review", json={"trust_state": "ignored"}),
        ]

        assert [response.status_code for response in checks] == [401, 401, 401, 401, 401, 401]
    finally:
        get_settings.cache_clear()


def test_document_and_source_update_routes_accept_valid_api_key(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", API_KEY)
    get_settings.cache_clear()
    store = DocumentUpdateStore(tmp_path)
    store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="candidate-auth-check",
                tracked_title="MCO 5000.1",
                trigger_type="manual_review",
            )
        ]
    )

    def override_store() -> DocumentUpdateStore:
        return store

    app.dependency_overrides[get_document_update_store] = override_store
    app.dependency_overrides[get_source_update_store] = override_store
    client = TestClient(app)
    headers = {"X-Local-API-Key": API_KEY}
    try:
        create_response = client.post(
            "/documents/check-updates",
            headers=headers,
            json=[],
        )
        assert create_response.status_code == 200

        list_response = client.get("/source-updates", headers=headers)
        assert list_response.status_code == 200
        assert list_response.json()
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


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
                "published_at": "2026-04-30T14:00:00Z",
            }
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidates"]
    assert payload["candidates"][0]["human_review_required"] is True
    assert payload["candidates"][0]["source_published_at"] == "2026-04-30T14:00:00Z"


def test_document_update_routes_persist_and_update_status(tmp_path: Path) -> None:
    from app.services.ingestion.document_update_store import DocumentUpdateStore
    from app.services.ingestion.source_state_store import SourceStateStore

    store = DocumentUpdateStore(tmp_path)
    state_store = SourceStateStore(tmp_path / "states")

    def override_update_store() -> DocumentUpdateStore:
        return store

    def override_source_state_store() -> SourceStateStore:
        return state_store

    app.dependency_overrides[get_document_update_store] = override_update_store
    app.dependency_overrides[get_document_source_state_store] = override_source_state_store
    client = TestClient(app)
    try:
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
        assert create_response.json()["candidates"][0]["trust_state"] == "needs_review"

        list_response = client.get("/documents/updates")
        assert list_response.status_code == 200
        assert list_response.json()

        status_response = client.post(
            f"/documents/updates/{candidate_id}/status",
            json={
                "review_status": "reviewed",
                "trust_state": "verified_current",
                "review_notes": "Verified against official page.",
            },
        )
        assert status_response.status_code == 200
        assert status_response.json()["review_status"] == "reviewed"
        assert status_response.json()["trust_state"] == "verified_current"

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
    finally:
        app.dependency_overrides.clear()


def test_source_updates_route_lists_and_reviews_trust_state(tmp_path: Path) -> None:
    store = DocumentUpdateStore(tmp_path)
    store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="candidate-trust",
                tracked_title="MCO 5000.1",
                trigger_type="manual_review",
            )
        ]
    )

    def override_store() -> DocumentUpdateStore:
        return store

    app.dependency_overrides[get_source_update_store] = override_store
    client = TestClient(app)
    try:
        list_response = client.get("/source-updates")
        assert list_response.status_code == 200
        assert list_response.json()[0]["trust_state"] == "needs_review"

        review_response = client.post(
            "/source-updates/candidate-trust/review",
            json={"trust_state": "update_detected", "review_notes": "New MARADMIN appears to supersede source."},
        )
        assert review_response.status_code == 200
        payload = review_response.json()
        assert payload["trust_state"] == "update_detected"
        assert payload["review_notes"] == "New MARADMIN appears to supersede source."
        assert payload["reviewed_at"] is not None
    finally:
        app.dependency_overrides.clear()


def test_document_update_store_loads_legacy_records_with_default_trust_state(tmp_path: Path) -> None:
    legacy_payload = {
        "candidate_id": "legacy-candidate",
        "tracked_title": "Legacy Source",
        "trigger_type": "manual_review",
        "detected_at": datetime(2026, 6, 3, tzinfo=UTC).isoformat(),
    }
    (tmp_path / "legacy-candidate.json").write_text(
        DocumentationUpdateCandidate(**legacy_payload).model_dump_json(exclude={"trust_state"}),
        encoding="utf-8",
    )

    record = DocumentUpdateStore(tmp_path).get("legacy-candidate")

    assert record is not None
    assert record.trust_state == "needs_review"
