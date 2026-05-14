from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class UpdateTriggerType(StrEnum):
    maradmin = "maradmin"
    mcpel_page = "mcpel_page"
    manifest_diff = "manifest_diff"
    manual_review = "manual_review"


class UpdateConfidence(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class UpdateReviewStatus(StrEnum):
    new = "new"
    reviewed = "reviewed"
    accepted = "accepted"
    ignored = "ignored"


class DocumentationUpdateCandidate(BaseModel):
    candidate_id: str
    tracked_source_id: str | None = None
    tracked_title: str
    trigger_type: UpdateTriggerType
    trigger_source_id: str | None = None
    trigger_url: str | None = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    matched_terms: list[str] = Field(default_factory=list)
    change_signals: list[str] = Field(default_factory=list)
    old_version: str | None = None
    new_version: str | None = None
    old_source_hash: str | None = None
    new_source_hash: str | None = None
    confidence: UpdateConfidence = UpdateConfidence.low
    review_status: UpdateReviewStatus = UpdateReviewStatus.new
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    human_review_required: bool = True
    warnings: list[str] = Field(default_factory=list)


class DocumentationUpdateScanResult(BaseModel):
    candidates: list[DocumentationUpdateCandidate]
    warnings: list[str] = Field(default_factory=list)


class DocumentationUpdateStatusUpdate(BaseModel):
    review_status: UpdateReviewStatus
    review_notes: str | None = None
