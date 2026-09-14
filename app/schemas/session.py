from datetime import UTC, date, datetime

from pydantic import BaseModel, Field


class PmeStatus(BaseModel):
    program: str
    status: str
    due_date: date | None = None
    notes: str | None = None


class FitrepReminder(BaseModel):
    occasion: str
    due_date: date | None = None
    role: str | None = None
    notes: str | None = None


class CareerTrend(BaseModel):
    label: str
    direction: str = "watch"
    evidence: list[str] = Field(default_factory=list)
    recommended_action: str | None = None


class CareerOpportunity(BaseModel):
    title: str
    opportunity_type: str
    due_date: date | None = None
    source_url: str | None = None
    notes: str | None = None


class DrillDateRecord(BaseModel):
    drill_date: date
    label: str | None = None


class RecurringCheck(BaseModel):
    title: str
    cadence: str = "each_drill"
    category: str = "admin"
    due_offset_days: int | None = None
    notes: str | None = None


class DrillHandoffEntry(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    label: str = Field(default="Drill handoff", max_length=200)
    date: str = Field(default="", max_length=40)
    admin: str = Field(default="", max_length=20000)
    drill: str = Field(default="", max_length=20000)
    archived: bool = False


class DrillHandoffJournalRequest(BaseModel):
    entries: list[DrillHandoffEntry] = Field(max_length=500)


class UserSessionHandoff(BaseModel):
    user_key: str
    display_name: str | None = None
    rank: str | None = None
    mos: str | None = None
    billet: str | None = None
    unit_id: str | None = None
    pme: list[PmeStatus] = Field(default_factory=list)
    fitreps: list[FitrepReminder] = Field(default_factory=list)
    drill_dates: list[DrillDateRecord] = Field(default_factory=list)
    recurring_drill_notes: list[str] = Field(default_factory=list)
    recurring_checks: list[RecurringCheck] = Field(default_factory=list)
    admin_watch_items: list[str] = Field(default_factory=list)
    # None denotes a legacy handoff that has not been opened in the journal.
    # An empty list denotes an intentionally empty/deleted journal.
    drill_handoffs: list[DrillHandoffEntry] | None = None
    rqs_context_id: str | None = None
    bio_context_id: str | None = None
    career_trends: list[CareerTrend] = Field(default_factory=list)
    career_opportunities: list[CareerOpportunity] = Field(default_factory=list)
    recommended_books: list[str] = Field(default_factory=list)
    recommended_courses: list[str] = Field(default_factory=list)
    preferences: dict[str, str] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)


class HandoffUpsertResponse(BaseModel):
    handoff: UserSessionHandoff
    message: str
