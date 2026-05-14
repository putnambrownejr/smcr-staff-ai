from datetime import UTC, datetime

from app.schemas.ingestion import MessageRecord
from app.services.ingestion.document_update_monitor import DocumentUpdateMonitor
from app.services.ingestion.maradmin_scraper import tag_message
from app.services.ingestion.rss_client import FeedItem


def test_maradmin_document_update_keywords_tag_message() -> None:
    item = FeedItem(
        title="MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
        link="https://example.test/maradmin",
        summary="This message announces an update published on MCPEL and effective immediately.",
    )

    tags = tag_message(item)

    assert "DocumentUpdate" in tags
    assert "Admin" in tags


def test_document_update_monitor_creates_candidate_from_maradmin() -> None:
    record = MessageRecord(
        source_id="maradmin-123-26",
        title="MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
        canonical_url="https://example.test/maradmin-123-26",
        published_at=datetime(2026, 5, 1, tzinfo=UTC),
        summary="This message announces an update to FitRep/PES policy published on MCPEL.",
        tags=["DocumentUpdate"],
        source_hash="abc123",
    )

    result = DocumentUpdateMonitor().scan_maradmin_records([record])

    assert result.candidates
    candidate = next(candidate for candidate in result.candidates if candidate.tracked_title == "PES / FitRep")
    assert candidate.tracked_title == "PES / FitRep"
    assert candidate.trigger_type == "maradmin"
    assert candidate.human_review_required is True
    assert candidate.confidence in {"medium", "high"}
