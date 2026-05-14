from pydantic import BaseModel, Field

from app.schemas.admin import AdminReadinessResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.source_updates import DocumentationUpdateCandidate


class DashboardWorkspaceResponse(BaseModel):
    mode: str
    user_key: str | None = None
    summary_lines: list[str] = Field(default_factory=list)
    chief_brief: ChiefBriefResponse
    admin_readiness: AdminReadinessResponse
    career_watch: CareerWatchResponse
    document_summary: PersonalDocumentSummary | None = None
    tracked_opportunities: list[OpportunityRecord] = Field(default_factory=list)
    documentation_updates: list[DocumentationUpdateCandidate] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
