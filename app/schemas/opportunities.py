from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.schemas.billets import BilletUserProfile


class OpportunityType(StrEnum):
    smcr = "smcr"
    ima = "ima"
    smcr_bic = "smcr_bic"
    ados = "ados"
    ia_jia = "ia_jia"
    other = "other"


class OpportunityRecord(BaseModel):
    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    unit: str | None = None
    location: str | None = None
    mos: str | None = None
    rank: str | None = None
    rank_min: str | None = None
    rank_max: str | None = None
    duration: str | None = None
    source_url: str | None = None
    direct_url: str | None = None
    source_name: str | None = None
    description: str | None = None
    notes: str | None = None
    published_at: date | None = None
    due_date: date | None = None
    source_order: int | None = None
    match_score: int | None = None
    match_reasons: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tracked: bool = False
    tracked_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator("opportunity_type", mode="before")
    @classmethod
    def normalize_legacy_smcr_type(cls, value: object) -> object:
        return OpportunityType.smcr if value == "smcr_bic" else value


class OpportunityRecommendation(BaseModel):
    opportunity: OpportunityRecord
    score: int
    match_reasons: list[str]
    warnings: list[str] = Field(default_factory=list)


class ManualOpportunityRequest(BaseModel):
    title: str
    opportunity_type: OpportunityType = OpportunityType.ados
    unit: str | None = None
    location: str | None = None
    mos: str | None = None
    rank: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    description: str | None = None
    notes: str | None = None
    due_date: date | None = None

    @field_validator("opportunity_type", mode="before")
    @classmethod
    def normalize_legacy_smcr_type(cls, value: object) -> object:
        return OpportunityType.smcr if value == "smcr_bic" else value


class OpportunityTrackRequest(BaseModel):
    user_key: str | None = None
    opportunities: list[ManualOpportunityRequest]


class OpportunityTrackResponse(BaseModel):
    tracked: list[OpportunityRecord]
    message: str


class OpportunityRecommendRequest(BaseModel):
    profile: BilletUserProfile
    opportunities: list[ManualOpportunityRequest]
    max_results: int = Field(default=10, ge=1, le=50)


class OpportunityRecommendResponse(BaseModel):
    recommendations: list[OpportunityRecommendation]
    warnings: list[str] = Field(default_factory=list)
