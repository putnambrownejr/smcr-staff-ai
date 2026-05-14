from datetime import date

from pydantic import BaseModel, Field

from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import UserSessionHandoff


class AdminReadinessItem(BaseModel):
    title: str
    category: str
    priority: str = "medium"
    due_date: date | None = None
    recommendation: str
    source: str | None = None


class AdminReadinessResponse(BaseModel):
    title: str
    user_key: str
    handoff: UserSessionHandoff | None = None
    summary_lines: list[str] = Field(default_factory=list)
    items: list[AdminReadinessItem] = Field(default_factory=list)
    document_summary: PersonalDocumentSummary | None = None
    warnings: list[str] = Field(default_factory=list)
