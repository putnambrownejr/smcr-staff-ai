from collections import Counter

from app.schemas.personal_documents import PersonalDocumentRecord, PersonalDocumentSummary, record_from_context
from app.services.storage.local_context_store import LocalContextStore

PERSONAL_DOCUMENT_WARNINGS = [
    "Personal documents are local user context, not canonical doctrine or official records.",
    "Do not store classified, CUI, secrets, or unnecessary PII in this prototype.",
]


class PersonalDocumentOrganizer:
    def __init__(self, context_store: LocalContextStore) -> None:
        self.context_store = context_store

    def list_documents(self, document_type: str | None = None) -> PersonalDocumentSummary:
        records = [record_from_context(item) for item in self.context_store.list()]
        if document_type:
            records = [record for record in records if record.document_type == document_type]
        return _summary(records)


def _summary(records: list[PersonalDocumentRecord]) -> PersonalDocumentSummary:
    by_type = Counter(record.document_type.value for record in records)
    return PersonalDocumentSummary(
        total_documents=len(records),
        by_type=dict(sorted(by_type.items())),
        pii_flagged_count=sum(record.contains_pii for record in records),
        records=records,
        warnings=PERSONAL_DOCUMENT_WARNINGS,
    )
