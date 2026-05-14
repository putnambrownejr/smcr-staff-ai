from datetime import date

from pydantic import BaseModel, Field

from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import CareerTrend, UserSessionHandoff


class CareerWatchItem(BaseModel):
    title: str
    category: str
    priority: str = "medium"
    due_date: date | None = None
    recommendation: str
    source: str | None = None


class CareerWatchResponse(BaseModel):
    title: str
    user_key: str
    handoff: UserSessionHandoff | None = None
    handoff_is_stale: bool = False
    watch_items: list[CareerWatchItem] = Field(default_factory=list)
    tracked_opportunities: list[OpportunityRecord] = Field(default_factory=list)
    document_summary: PersonalDocumentSummary | None = None
    recommended_books: list[str] = Field(default_factory=list)
    recommended_courses: list[str] = Field(default_factory=list)
    career_trends: list[CareerTrend] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
