from datetime import date
from pathlib import Path

from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.storage.local_context_store import LocalContextStore


def test_personal_document_organizer_summarizes_local_context(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    store.save(
        filename="bio.txt",
        content=b"BIO draft with phone: 555-123-4567",
        content_type="text/plain",
        document_type="bio",
        tags=["career"],
        review_date=date(2026, 1, 1),
    )
    store.save(
        filename="orders.txt",
        content=b"Training-only orders placeholder.",
        content_type="text/plain",
        document_type="orders",
        tags=["travel"],
        expiration_date=date(2026, 1, 1),
    )

    organizer = PersonalDocumentOrganizer(store)
    summary = organizer.list_documents()

    assert summary.total_documents == 2
    assert summary.by_type["bio"] == 1
    assert summary.by_type["orders"] == 1
    assert summary.pii_flagged_count == 1
    assert "rqs" in summary.missing_recommended_types
    assert "pme_certificate" in summary.missing_recommended_types
    assert summary.review_due_count == 1
    assert summary.expired_count == 1

    detail = organizer.get_document(summary.records[0].context_id)
    assert detail is not None
    assert detail.record.review_date is not None or detail.record.expiration_date is not None
    assert detail.text_preview
