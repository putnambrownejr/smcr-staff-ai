from collections import Counter
from datetime import UTC, datetime

from app.schemas.personal_documents import (
    PersonalDocumentDetail,
    PersonalDocumentRecord,
    PersonalDocumentSummary,
    record_from_context,
)
from app.services.storage.local_context_store import LocalContextStore

PERSONAL_DOCUMENT_WARNINGS = [
    "Personal documents are local user context, not canonical doctrine or official records.",
    "Do not store classified, CUI, secrets, or unnecessary PII in this prototype.",
]
RECOMMENDED_DOCUMENT_TYPES = ["rqs", "bio", "orders", "pme_certificate"]


class PersonalDocumentOrganizer:
    def __init__(self, context_store: LocalContextStore) -> None:
        self.context_store = context_store

    def list_documents(self, document_type: str | None = None) -> PersonalDocumentSummary:
        records = [record_from_context(item) for item in self.context_store.list()]
        if document_type:
            records = [record for record in records if record.document_type == document_type]
        return _summary(records)

    def get_document(self, context_id: str) -> PersonalDocumentDetail | None:
        item = self.context_store.get(context_id)
        preview = self.context_store.read_preview(context_id)
        if item is None or preview is None:
            return None
        return PersonalDocumentDetail(record=record_from_context(item), text_preview=preview)


def _summary(records: list[PersonalDocumentRecord]) -> PersonalDocumentSummary:
    now = datetime.now(UTC).date()
    by_type = Counter(record.document_type.value for record in records)
    present_types = set(by_type)
    return PersonalDocumentSummary(
        total_documents=len(records),
        by_type=dict(sorted(by_type.items())),
        pii_flagged_count=sum(record.contains_pii for record in records),
        missing_recommended_types=[
            doc_type for doc_type in RECOMMENDED_DOCUMENT_TYPES if doc_type not in present_types
        ],
        review_due_count=sum(record.review_date is not None and record.review_date <= now for record in records),
        expired_count=sum(record.expiration_date is not None and record.expiration_date < now for record in records),
        records=records,
        warnings=PERSONAL_DOCUMENT_WARNINGS,
    )
