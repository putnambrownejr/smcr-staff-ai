from pydantic import BaseModel, Field

from app.schemas.actions import ActionRecord
from app.schemas.admin import AdminReadinessResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.history import TodayInMarineHistoryItem
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.reading_state import ReadingProgressRecord
from app.schemas.source_updates import DocumentationUpdateCandidate


class DailyOpsEntry(BaseModel):
    title: str
    detail: str | None = None
    category: str | None = None
    priority: str = "medium"
    due_date: str | None = None


class DailyOpsBrief(BaseModel):
    executive_snapshot: list[str] = Field(default_factory=list)
    must_do: list[DailyOpsEntry] = Field(default_factory=list)
    should_do: list[DailyOpsEntry] = Field(default_factory=list)
    can_defer: list[DailyOpsEntry] = Field(default_factory=list)
    waiting_on: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    leverage_actions: list[str] = Field(default_factory=list)
    prep_follow_ups: list[str] = Field(default_factory=list)


class AnalystBrief(BaseModel):
    executive_summary: list[str] = Field(default_factory=list)
    data_quality_notes: list[str] = Field(default_factory=list)
    kpi_summary: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    likely_causes: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    follow_up_checks: list[str] = Field(default_factory=list)


class DashboardDocumentDetail(BaseModel):
    context_id: str
    filename: str
    document_type: str
    contains_pii: bool
    review_date: str | None = None
    expiration_date: str | None = None
    text_preview: str


class DashboardTemplateReference(BaseModel):
    template_id: str
    template_name: str
    template_type: str
    template_source: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    preferred_format: str | None = None
    reusable_headings: list[str] = Field(default_factory=list)
    reusable_guidance: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DashboardReadingBook(BaseModel):
    slug: str
    title: str
    author: str
    categories: list[str] = Field(default_factory=list)
    open_source_available: bool = False
    summary: str
    key_themes: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    progress: ReadingProgressRecord | None = None


class DashboardTickerItem(BaseModel):
    title: str
    status: str
    summary: str
    source_url: str | None = None


class DashboardWorkspaceResponse(BaseModel):
    mode: str
    user_key: str | None = None
    summary_lines: list[str] = Field(default_factory=list)
    chief_brief: ChiefBriefResponse
    admin_readiness: AdminReadinessResponse
    career_watch: CareerWatchResponse
    daily_ops_brief: DailyOpsBrief
    analyst_brief: AnalystBrief
    document_summary: PersonalDocumentSummary | None = None
    tracked_actions: list[ActionRecord] = Field(default_factory=list)
    tracked_opportunities: list[OpportunityRecord] = Field(default_factory=list)
    documentation_updates: list[DocumentationUpdateCandidate] = Field(default_factory=list)
    document_details: list[DashboardDocumentDetail] = Field(default_factory=list)
    template_library: list[DashboardTemplateReference] = Field(default_factory=list)
    maradmin_ticker: list[DashboardTickerItem] = Field(default_factory=list)
    today_in_history: list[TodayInMarineHistoryItem] = Field(default_factory=list)
    reading_books: list[DashboardReadingBook] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
