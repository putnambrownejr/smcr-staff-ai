from pydantic import BaseModel, Field

from app.schemas.actions import ActionRecord
from app.schemas.admin import AdminReadinessResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
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
    warnings: list[str] = Field(default_factory=list)
