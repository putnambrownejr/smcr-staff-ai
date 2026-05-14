import pytest
from pydantic import ValidationError

from app.schemas.documents import IngestRequest


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
