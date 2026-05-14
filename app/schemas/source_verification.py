from pydantic import BaseModel, Field

from app.schemas.sources import ManifestValidationResult, SourceRef


class SourceVerificationRequest(BaseModel):
    manifest_path: str | None = None
    refs: list[SourceRef] = Field(default_factory=list)


class SourceVerificationFinding(BaseModel):
    title: str
    verification_status: str
    classification_label: str
    eligible_for_public_prototype: bool
    warnings: list[str] = Field(default_factory=list)


class SourceVerificationResponse(BaseModel):
    manifest_validation: ManifestValidationResult | None = None
    findings: list[SourceVerificationFinding] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
