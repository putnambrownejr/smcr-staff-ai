from datetime import date, datetime

from pydantic import BaseModel, Field


class ExternalAiPacketRequest(BaseModel):
    user_key: str
    include_handoff: bool = True
    include_active_user_context: bool = True
    include_document_summary: bool = False
    include_drill_plans: bool = False
    include_opportunities: bool = False
    include_recommendations: bool = True
    purpose: str | None = None


class ShareSafeHandoff(BaseModel):
    mos: str | None = None
    billet: str | None = None
    unit_id: str | None = None
    pme: list[dict[str, str | None]] = Field(default_factory=list)
    fitreps: list[dict[str, str | None]] = Field(default_factory=list)
    drill_dates: list[dict[str, date | str | None]] = Field(default_factory=list)
    recurring_drill_notes: list[str] = Field(default_factory=list)
    recurring_checks: list[dict[str, str | int | None]] = Field(default_factory=list)
    admin_watch_items: list[str] = Field(default_factory=list)
    career_trends: list[dict[str, str | list[str] | None]] = Field(default_factory=list)
    recommended_books: list[str] = Field(default_factory=list)
    recommended_courses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ShareSafeActiveContext(BaseModel):
    unit_name: str | None = None
    unit_type: str | None = None
    unit_family: str | None = None
    billet_override: str | None = None
    mos_override: str | None = None
    current_focus: list[str] = Field(default_factory=list)
    staff_bias: list[str] = Field(default_factory=list)
    temporary_notes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)


class ShareSafeDocumentSummary(BaseModel):
    total_documents: int
    by_type: dict[str, int]
    pii_flagged_count: int
    missing_recommended_types: list[str] = Field(default_factory=list)
    review_due_count: int
    expired_count: int
    warnings: list[str] = Field(default_factory=list)


class ShareSafeDrillPlan(BaseModel):
    id: str
    drill_date: date
    tasks: list[dict[str, str | int | date | bool]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ShareSafeOpportunity(BaseModel):
    title: str
    opportunity_type: str
    unit: str | None = None
    location: str | None = None
    mos: str | None = None
    rank: str | None = None
    due_date: date | None = None
    warnings: list[str] = Field(default_factory=list)


class ExternalAiPacketResponse(BaseModel):
    user_key: str
    purpose: str | None = None
    safe_to_share: bool = True
    handoff: ShareSafeHandoff | None = None
    active_user_context: ShareSafeActiveContext | None = None
    document_summary: ShareSafeDocumentSummary | None = None
    drill_plans: list[ShareSafeDrillPlan] = Field(default_factory=list)
    opportunities: list[ShareSafeOpportunity] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    withheld_categories: list[str] = Field(default_factory=list)
    redacted_fields: list[str] = Field(default_factory=list)
    recommended_share_prompt: str | None = None
