from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class VerifiedSourceStatus(StrEnum):
    current = "current"
    watch = "watch"
    superseded = "superseded"
    needs_review = "needs_review"


class VerifiedSourceState(BaseModel):
    source_state_id: str
    tracked_source_id: str | None = None
    tracked_title: str
    status: VerifiedSourceStatus = VerifiedSourceStatus.current
    current_version: str | None = None
    current_source_hash: str | None = None
    verification_source_url: str | None = None
    accepted_candidate_id: str | None = None
    last_verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None


class SourceStateAcceptRequest(BaseModel):
    status: VerifiedSourceStatus = VerifiedSourceStatus.current
    current_version: str | None = None
    current_source_hash: str | None = None
    verification_source_url: str | None = None
    notes: str | None = None


class SourceTrustMarker(BaseModel):
    tracked_title: str
    status: VerifiedSourceStatus = VerifiedSourceStatus.needs_review
    verification_source_url: str | None = None
    last_verified_at: datetime | None = None
    notes: str | None = None
