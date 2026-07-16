from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.agents import StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus

SOURCE_LIBRARY_DRAFT_FOOTER = "DRAFT — Verify all references against current official sources before acting."


class SourceLifecycle(StrEnum):
    active = "active"
    stale = "stale"
    removed = "removed"
    rejected = "rejected"


class SourceFetchRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2_048)
    title: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=500)


class SourceFetchPreview(BaseModel):
    url: str
    host: str
    expected_call_count: int = Field(default=1, ge=1, le=1)
    approval_digest: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    finding_categories: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SourceFetchApproval(BaseModel):
    approval_digest: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    acknowledged: bool
    acknowledged_finding_categories: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_acknowledgement(self) -> SourceFetchApproval:
        if not self.acknowledged:
            raise ValueError("Source fetch approval requires acknowledgement.")
        return self


class SavedSource(BaseModel):
    source_id: str = Field(min_length=1)
    user_key_digest: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    original_url: str
    canonical_url: str
    title: str
    publisher: str | None = None
    media_type: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)
    lifecycle: SourceLifecycle = SourceLifecycle.active
    trust_status: VerifiedSourceStatus = VerifiedSourceStatus.needs_review
    classification_label: str = "UNCLASSIFIED"
    cui_flag: bool = False
    raw_content_path: str
    normalized_text_path: str
    chunks_path: str
    chunk_count: int = Field(ge=0)
    document_version: str | None = None
    effective_date: str | None = None
    last_rechecked_at: datetime | None = None
    review_notes: str | None = None


class SourceRetrieveRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    query: str = Field(min_length=1, max_length=5_000)
    source_ids: list[str] | None = None
    limit: int = Field(default=5, ge=1, le=20)


class SourceRetrieveResult(BaseModel):
    excerpt: str
    citation: StructuredCitation
    source_trust: SourceTrustMarker


class SourceRetrieveResponse(BaseModel):
    results: list[SourceRetrieveResult] = Field(default_factory=list)
    advisory_footer: str = SOURCE_LIBRARY_DRAFT_FOOTER
