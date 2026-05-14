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
    )
    store.save(
        filename="orders.txt",
        content=b"Training-only orders placeholder.",
        content_type="text/plain",
        document_type="orders",
        tags=["travel"],
    )

    summary = PersonalDocumentOrganizer(store).list_documents()

    assert summary.total_documents == 2
    assert summary.by_type["bio"] == 1
    assert summary.by_type["orders"] == 1
    assert summary.pii_flagged_count == 1
