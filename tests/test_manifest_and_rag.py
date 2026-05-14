from datetime import datetime
from pathlib import Path

from app.schemas.documents import DocumentRead
from app.schemas.sources import validate_manifest
from app.services.rag.pipeline import LocalRagPipeline


def test_manifest_validation_reports_placeholder_sources() -> None:
    result = validate_manifest(Path("data/seed/doctrine_manifest.example.yaml"))

    assert result.category_count > 0
    assert result.source_ref_count > 0
    assert result.placeholder_count > 0
    assert result.warnings


def test_rag_pipeline_preserves_structured_citation_metadata() -> None:
    document = DocumentRead(
        source_id="mcdp-1",
        title="MCDP 1 Warfighting",
        publication_type="doctrine",
        issuing_org="USMC",
        url="https://example.test/mcdp-1",
        retrieved_at=datetime(2026, 1, 1),
        version="example",
        classification_label="UNCLASSIFIED",
        cui_flag=False,
        source_hash="abc123",
    )
    pipeline = LocalRagPipeline()

    count = pipeline.ingest_text(document, "Maneuver warfare requires tempo and initiative.")
    results = pipeline.retrieve("tempo initiative")

    assert count == 1
    assert results[0].citation.title == "MCDP 1 Warfighting"
    assert results[0].citation.source_hash == "abc123"
    assert results[0].citation.chunk_id is not None
