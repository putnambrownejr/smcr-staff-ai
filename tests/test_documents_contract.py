import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.documents import IngestRequest


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
