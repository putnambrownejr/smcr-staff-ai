from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.opportunities import OpportunityRecord, OpportunityType


class CareerOpportunitySortField(StrEnum):
    source_order = "source_order"
    by_title = "title"
    opportunity_type = "opportunity_type"
    rank = "rank"
    mos = "mos"
    unit = "unit"
    location = "location"
    duration = "duration"
    published_at = "published_at"
    due_date = "due_date"
    match_score = "match_score"


class SortDirection(StrEnum):
    ascending = "ascending"
    descending = "descending"


class OpportunityQuery(BaseModel):
    sort_by: CareerOpportunitySortField = CareerOpportunitySortField.source_order
    direction: SortDirection = SortDirection.ascending
    opportunity_types: list[OpportunityType] = Field(default_factory=list)
    rank: str | None = None
    mos: str | None = None
    location: str | None = None
    source: str | None = None
    keyword: str | None = None


class OpportunitySourceKey(StrEnum):
    reserve_billets = "reserve_billets"
    active_billets = "active_billets"


class OpportunitySource(BaseModel):
    key: OpportunitySourceKey
    name: str
    url: str
    default_type: OpportunityType
    description: str = ""


class OpportunityRefreshOutcome(StrEnum):
    listings_refreshed = "listings_refreshed"
    link_only = "link_only"
    failed_cached = "failed_cached"
    failed_no_cache = "failed_no_cache"


class OpportunityParseResult(BaseModel):
    source: OpportunitySource
    records: list[OpportunityRecord] = Field(default_factory=list)
    official_links: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CareerOpportunitySourceState(BaseModel):
    source: OpportunitySource
    outcome: OpportunityRefreshOutcome
    records: list[OpportunityRecord] = Field(default_factory=list)
    official_links: list[str] = Field(default_factory=list)
    refreshed_at: datetime | None = None
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_successful_at: datetime | None = None
    last_error: str | None = None
    warnings: list[str] = Field(default_factory=list)


class CareerOpportunityRefreshAllResponse(BaseModel):
    results: list[CareerOpportunitySourceState] = Field(default_factory=list)


class CareerOpportunityListResponse(BaseModel):
    total_records: int
    records: list[OpportunityRecord] = Field(default_factory=list)
    sources: list[CareerOpportunitySourceState] = Field(default_factory=list)
