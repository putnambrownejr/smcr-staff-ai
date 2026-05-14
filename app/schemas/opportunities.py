from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.billets import BilletUserProfile


class OpportunityType(StrEnum):
    smcr_bic = "smcr_bic"
    ados = "ados"


class OpportunityRecord(BaseModel):
    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    unit: str | None = None
    location: str | None = None
    mos: str | None = None
    rank: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    description: str | None = None
    notes: str | None = None
    due_date: date | None = None
    tracked: bool = True
    tracked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)


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
