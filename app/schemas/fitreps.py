from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class FitrepSourceType(StrEnum):
    manual = "manual"
    my_record_import = "my_record_import"
    rs_profile_import = "rs_profile_import"
    existing_tracker = "existing_tracker"


class FitrepReportCreateRequest(BaseModel):
    user_key: str
    period_start: date | None = None
    period_end: date | None = None
    occasion: str = ""
    grade: str = ""
    billet: str = ""
    unit: str = ""
    rs_label: str = ""
    ro_label: str = ""
    relative_value: Decimal | None = None
    cumulative_relative_value: Decimal | None = None
    comparative_assessment: int | None = Field(default=None, ge=1, le=8)
    traits: dict[str, float] = Field(default_factory=dict)
    accomplishments: list[str] = Field(default_factory=list)
    development_observations: list[str] = Field(default_factory=list)
    private_notes: str = ""
    source_type: FitrepSourceType = FitrepSourceType.manual
    source_context_id: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class FitrepReport(FitrepReportCreateRequest):
    report_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RsProfileSnapshotCreateRequest(BaseModel):
    user_key: str
    rs_label: str = ""
    as_of_date: date | None = None
    grade: str = ""
    population_size: int | None = Field(default=None, ge=0)
    report_count: int | None = Field(default=None, ge=0)
    relative_value_average: Decimal | None = None
    profile_notes: str = ""
    source_type: FitrepSourceType = FitrepSourceType.manual
    source_context_id: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class RsProfileSnapshot(RsProfileSnapshotCreateRequest):
    snapshot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FitrepImprovementGoalRequest(BaseModel):
    user_key: str
    goal_id: str | None = None
    rs_label: str
    title: str = Field(min_length=1)
    target_date: date | None = None
    status: str = "active"
    evidence: list[str] = Field(default_factory=list)
    notes: str = ""


class FitrepImprovementGoal(FitrepImprovementGoalRequest):
    goal_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FitrepWorkspace(BaseModel):
    user_key: str
    reports: list[FitrepReport] = Field(default_factory=list)
    rs_profiles: list[RsProfileSnapshot] = Field(default_factory=list)
    goals: list[FitrepImprovementGoal] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FitrepImportKind(StrEnum):
    my_record = "my_record"
    rs_profile = "rs_profile"


class FitrepImportPreviewRequest(BaseModel):
    user_key: str
    context_id: str
    kind: FitrepImportKind


class FitrepImportProposal(BaseModel):
    kind: FitrepImportKind
    report: FitrepReportCreateRequest | None = None
    rs_profile: RsProfileSnapshotCreateRequest | None = None
    warnings: list[str] = Field(default_factory=list)
    requires_confirmation: bool = True


class FitrepImportConfirmRequest(BaseModel):
    user_key: str
    kind: FitrepImportKind
    proposal: FitrepImportProposal


class FitrepTrendPoint(BaseModel):
    report_id: str
    label: str
    value: Decimal


class FitrepRsSummary(BaseModel):
    rs_label: str
    report_count: int
    average_relative_value: Decimal | None = None
    minimum_relative_value: Decimal | None = None
    maximum_relative_value: Decimal | None = None


class FitrepAnalyticsResponse(BaseModel):
    sample_size: int
    relative_value_trend: list[FitrepTrendPoint] = Field(default_factory=list)
    trait_trends: dict[str, list[FitrepTrendPoint]] = Field(default_factory=dict)
    by_reporting_senior: list[FitrepRsSummary] = Field(default_factory=list)
    comparative_assessment_distribution: dict[int, int] = Field(default_factory=dict)
    data_quality_warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Descriptive analysis of user-confirmed data only; it does not predict promotion, selection, or future marks."
    )
