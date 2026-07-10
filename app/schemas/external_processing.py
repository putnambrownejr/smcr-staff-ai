from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DisclosureMode(StrEnum):
    local_only = "local_only"
    sanitized = "sanitized"
    original = "original"


class ExternalProcessingSeverity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ExternalProcessingOutcome(StrEnum):
    completed = "completed"
    failed = "failed"
    local_only = "local_only"
    stale = "stale"


class ExternalProcessingFinding(BaseModel):
    category: str
    severity: ExternalProcessingSeverity
    message: str
    field_path: str


class ExternalProcessingMessage(BaseModel):
    role: Literal["system", "user"]
    content: str


class ExternalProcessingApproval(BaseModel):
    disclosure_mode: DisclosureMode
    approval_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    acknowledged_finding_categories: list[str] = Field(default_factory=list)
    acknowledged: bool = False

    @model_validator(mode="after")
    def validate_external_approval(self) -> ExternalProcessingApproval:
        if self.disclosure_mode is DisclosureMode.local_only:
            return self
        if not self.approval_digest:
            raise ValueError("External processing requires an approval digest.")
        if not self.acknowledged:
            raise ValueError("External processing requires explicit acknowledgement.")
        return self


class ExternalProcessingPreview(BaseModel):
    required: bool
    external_available: bool
    provider: str | None = None
    model: str | None = None
    expected_call_count: int = 0
    scope_label: str
    original_preview: list[ExternalProcessingMessage] = Field(default_factory=list)
    sanitized_preview: list[ExternalProcessingMessage] = Field(default_factory=list)
    findings: list[ExternalProcessingFinding] = Field(default_factory=list)
    finding_categories: list[str] = Field(default_factory=list)
    redacted_fields: list[str] = Field(default_factory=list)
    approval_digest: str | None = None
    payload_digest: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ExternalProcessingAuditEntry(BaseModel):
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scope_label: str
    user_key_digest: str
    provider: str | None = None
    model: str | None = None
    disclosure_mode: DisclosureMode
    finding_categories: list[str] = Field(default_factory=list)
    approval_digest: str | None = None
    payload_digest: str | None = None
    expected_call_count: int = 0
    completed_call_count: int = 0
    outcome: ExternalProcessingOutcome


class ExternalProcessingAuditLog(BaseModel):
    entries: list[ExternalProcessingAuditEntry] = Field(default_factory=list)
