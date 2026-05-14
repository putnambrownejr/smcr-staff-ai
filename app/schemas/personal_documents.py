from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.context import LocalContextMetadata


class PersonalDocumentType(StrEnum):
    rqs = "rqs"
    bio = "bio"
    orders = "orders"
    travel_receipt = "travel_receipt"
    dts = "dts"
    pme_certificate = "pme_certificate"
    medical_readiness = "medical_readiness"
    dental_readiness = "dental_readiness"
    fitrep = "fitrep"
    drill_plan = "drill_plan"
    other = "other"


class PersonalDocumentRecord(BaseModel):
    context_id: str
    filename: str
    document_type: PersonalDocumentType
    tags: list[str] = Field(default_factory=list)
    uploaded_at: datetime
    size_bytes: int
    contains_pii: bool = False
    retention_policy: str = "user_managed_local"
    review_date: date | None = None
    expiration_date: date | None = None
    advisory_only: bool = True
    warnings: list[str] = Field(default_factory=list)


class PersonalDocumentDetail(BaseModel):
    record: PersonalDocumentRecord
    text_preview: str


class PersonalDocumentSummary(BaseModel):
    total_documents: int
    by_type: dict[str, int]
    pii_flagged_count: int
    missing_recommended_types: list[str]
    review_due_count: int
    expired_count: int
    records: list[PersonalDocumentRecord]
    warnings: list[str] = Field(default_factory=list)


def record_from_context(item: LocalContextMetadata) -> PersonalDocumentRecord:
    allowed_types = {document_type.value for document_type in PersonalDocumentType}
    doc_type = item.document_type if item.document_type in allowed_types else PersonalDocumentType.other
    return PersonalDocumentRecord(
        context_id=item.context_id,
        filename=item.filename,
        document_type=PersonalDocumentType(doc_type),
        tags=item.tags,
        uploaded_at=item.uploaded_at,
        size_bytes=item.size_bytes,
        contains_pii=item.contains_pii,
        retention_policy=item.retention_policy,
        review_date=item.review_date,
        expiration_date=item.expiration_date,
        advisory_only=item.advisory_only,
        warnings=item.warnings,
    )
