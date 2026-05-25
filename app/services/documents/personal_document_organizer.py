from collections import Counter
from datetime import UTC, datetime

from app.schemas.personal_documents import (
    PersonalDocumentDetail,
    PersonalDocumentRecord,
    PersonalDocumentSummary,
    PersonalDocumentType,
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

    def update_document_type(self, context_id: str, document_type: str) -> PersonalDocumentRecord | None:
        item = self.context_store.update_document_type(context_id, document_type)
        if item is None:
            return None
        return record_from_context(item)

    def suggest_document_type(self, detail: PersonalDocumentDetail) -> tuple[str, str] | None:
        current = detail.record.document_type.value
        filename = detail.record.filename.lower()
        preview = detail.text_preview.lower()
        haystack = f"{filename}\n{preview}"

        if any(token in haystack for token in ("template", "format", "boilerplate", "sample", "example")):
            return _suggest_if_better(current, PersonalDocumentType.product_template.value, "Template-style filename or preview text.")

        if any(token in haystack for token in ("fitrep", "pes", "performance evaluation system")):
            return _suggest_if_better(current, PersonalDocumentType.fitrep.value, "FitRep or PES wording detected.")

        if any(token in haystack for token in ("1020.34", "uniform regulations", "uniform board", "uniform")):
            return _suggest_if_better(current, PersonalDocumentType.admin_reference.value, "Uniform-reference wording detected.")

        if any(token in haystack for token in ("mcdp", "mcwp", "mcrp", "mctp", "navmc", "marine corps planning process")):
            return _suggest_if_better(current, PersonalDocumentType.doctrine.value, "Doctrine publication pattern detected.")

        if any(
            token in haystack
            for token in (
                "maradmin",
                "mco ",
                "mcbul",
                "reserve administrative management manual",
                "dts",
                "gtcc",
                "travel explorer",
                "admin ch-",
            )
        ):
            return _suggest_if_better(current, PersonalDocumentType.admin_reference.value, "Administrative order or message pattern detected.")

        if any(
            token in haystack
            for token in (
                "student outline",
                "course book",
                "training",
                "case study",
                "ied",
                "familiarization",
                "range safety",
            )
        ):
            return _suggest_if_better(current, PersonalDocumentType.training_reference.value, "Training-reference wording detected.")

        return None


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


def _suggest_if_better(current: str, suggested: str, reason: str) -> tuple[str, str] | None:
    if current == suggested:
        return None
    if current not in {
        PersonalDocumentType.reference_note.value,
        PersonalDocumentType.other.value,
        PersonalDocumentType.training_media.value,
    }:
        return None
    return suggested, reason
