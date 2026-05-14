from pathlib import Path

from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.storage.local_context_store import LocalContextStore


def test_training_media_is_classified_as_personal_document_type(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    store.save(
        filename="use_case.mp4",
        content=b"\x00\x00\x00\x18ftypmp42",
        content_type="video/mp4",
        document_type="training_media",
        tags=["video", "use_case"],
        consent_ack=True,
    )

    summary = PersonalDocumentOrganizer(store).list_documents()

    assert summary.by_type["training_media"] == 1
    assert summary.records[0].document_type.value == "training_media"
