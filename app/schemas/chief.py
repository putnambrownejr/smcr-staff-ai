from datetime import date

from pydantic import BaseModel, Field

from app.schemas.calendar import DrillPrepPlanResponse
from app.schemas.ingestion import MessageRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate


class ChiefBriefRequest(BaseModel):
    user_key: str | None = None
    include_personal_documents: bool = True
    include_drill_plans: bool = True
    maradmin_records: list[MessageRecord] = Field(default_factory=list)


class ChiefActionItem(BaseModel):
    title: str
    category: str
    priority: str = "medium"
    due_date: date | None = None
    source: str | None = None
    recommendation: str


class ChiefBriefResponse(BaseModel):
    title: str
    user_key: str | None = None
    handoff: UserSessionHandoff | None = None
    action_items: list[ChiefActionItem]
    document_summary: PersonalDocumentSummary | None = None
    drill_plans: list[DrillPrepPlanResponse] = Field(default_factory=list)
    documentation_updates: list[DocumentationUpdateCandidate] = Field(default_factory=list)
    reading_recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
