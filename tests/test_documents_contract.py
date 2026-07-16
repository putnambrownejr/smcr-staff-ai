from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.routes.documents import get_source_library_service
from app.main import app
from app.schemas.documents import IngestRequest
from app.services.source_library.fetcher import PublicSourceFetcher
from app.services.source_library.service import SourceLibraryService
from app.services.source_library.store import SourceLibraryStore


def test_list_documents_returns_honest_empty_until_ingestion_is_wired() -> None:
    client = TestClient(app)

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == []


def test_ingest_request_requires_exactly_one_source() -> None:
    with pytest.raises(ValidationError):
        IngestRequest(source_type="manifest")

    with pytest.raises(ValidationError):
        IngestRequest(
            source_type="manifest",
            local_path="data/seed/doctrine_manifest.example.yaml",
            url="https://example.test/manifest.yaml",
        )


def test_ingest_request_requires_compatible_source_field() -> None:
    with pytest.raises(ValidationError):
        IngestRequest(source_type="rss", local_path="tests/fixtures/sample_maradmin_feed.xml")

    with pytest.raises(ValidationError):
        IngestRequest(source_type="pdf", url="https://example.test/file.pdf")

    request = IngestRequest(source_type="manifest", local_path="data/seed/doctrine_manifest.example.yaml")
    assert request.local_path == "data/seed/doctrine_manifest.example.yaml"


def test_ingest_request_allows_relative_local_paths_only_at_schema_level() -> None:
    request = IngestRequest(source_type="manifest", local_path="..\\..\\somewhere.yaml")
    assert request.local_path == "..\\..\\somewhere.yaml"


def test_source_library_fetch_list_retrieve_recheck_review_and_remove(tmp_path: Path) -> None:
    body = {"value": b"<html><title>Public plan</title><body>Public text for planning</body></html>"}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html"}, content=body["value"], request=request)

    service = SourceLibraryService(
        SourceLibraryStore(tmp_path / "source-library"),
        PublicSourceFetcher(
            lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False), max_bytes=1_024
        ),
    )
    app.dependency_overrides[get_source_library_service] = lambda: service
    try:
        client = TestClient(app)
        preview = client.post(
            "/documents/source-library/preview", json={"user_key": "u", "url": "https://example.test/a"}
        )
        assert preview.status_code == 200
        preview_payload = preview.json()
        fetched = client.post(
            "/documents/source-library/fetch",
            json={
                "user_key": "u",
                "url": "https://example.test/a",
                "preview": preview_payload,
                "approval": {
                    "approval_digest": preview_payload["approval_digest"],
                    "acknowledged": True,
                    "acknowledged_finding_categories": preview_payload["finding_categories"],
                },
            },
        )
        assert fetched.status_code == 200
        source = fetched.json()
        assert source["trust_status"] == "needs_review"

        listed = client.get("/documents/source-library?user_key=u")
        results = client.post("/documents/source-library/retrieve", json={"user_key": "u", "query": "public text"})
        assert listed.status_code == results.status_code == 200
        assert results.json()["results"][0]["citation"]["source_hash"] == source["content_hash"]

        body["value"] = b"<html><title>Public plan</title><body>Changed public text</body></html>"
        recheck_preview = client.post(f"/documents/source-library/{source['source_id']}/recheck-preview?user_key=u")
        assert recheck_preview.status_code == 200
        recheck_preview_payload = recheck_preview.json()
        rechecked = client.post(
            f"/documents/source-library/{source['source_id']}/recheck",
            json={
                "user_key": "u",
                "preview": recheck_preview_payload,
                "approval": {
                    "approval_digest": recheck_preview_payload["approval_digest"],
                    "acknowledged": True,
                    "acknowledged_finding_categories": recheck_preview_payload["finding_categories"],
                },
            },
        )
        assert rechecked.status_code == 200
        assert rechecked.json()["content_changed"] is True
        assert rechecked.json()["source"]["content_hash"] == source["content_hash"]
        assert rechecked.json()["source"]["trust_status"] == "watch"

        reviewed = client.post(
            f"/documents/source-library/{source['source_id']}/review",
            json={"user_key": "u", "status": "current", "notes": "Reviewed against publisher."},
        )
        assert reviewed.status_code == 200
        assert reviewed.json()["trust_status"] == "current"
        assert client.post(
            f"/documents/source-library/{source['source_id']}/recheck-preview?user_key=other"
        ).status_code == 404

        deleted = client.delete(f"/documents/source-library/{source['source_id']}?user_key=u")
        assert deleted.status_code == 200
        assert deleted.json() == {"removed": True}
    finally:
        app.dependency_overrides.pop(get_source_library_service, None)
