from enum import StrEnum

from pydantic import BaseModel, Field


class PrivacyFindingSeverity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class RepoPrivacySweepRequest(BaseModel):
    repo_root: str | None = None
    include_untracked: bool = True
    include_ignored_status: bool = True


class PrivacyFinding(BaseModel):
    severity: PrivacyFindingSeverity
    category: str
    title: str
    detail: str
    affected_paths: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class RepoPrivacySweepResponse(BaseModel):
    repo_root: str
    git_available: bool
    safe_to_push: bool
    staged_files: list[str] = Field(default_factory=list)
    unstaged_files: list[str] = Field(default_factory=list)
    untracked_files: list[str] = Field(default_factory=list)
    ignored_high_risk_paths: list[str] = Field(default_factory=list)
    findings: list[PrivacyFinding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
