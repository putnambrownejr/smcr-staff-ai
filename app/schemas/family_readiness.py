from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ReadinessDurationBand(StrEnum):
    short = "short"
    medium = "medium"
    long = "long"
    custom = "custom"


class ReadinessEventStatus(StrEnum):
    planning = "planning"
    active = "active"
    reintegration = "reintegration"
    archived = "archived"


class ReadinessItemStatus(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    complete = "complete"
    not_applicable = "not_applicable"


class ReadinessItemCategory(StrEnum):
    administration = "administration"
    legal = "legal"
    deers = "deers"
    household = "household"
    contacts = "contacts"
    opsec = "opsec"
    family_support = "family_support"
    reintegration = "reintegration"


class FamilyReadinessChecklistItem(BaseModel):
    item_id: str
    category: ReadinessItemCategory
    task: str
    plain_language: str
    status: ReadinessItemStatus = ReadinessItemStatus.not_started
    responsible_label: str = ""
    target_date: date | None = None
    notes: str = ""
    source_url: str | None = None
    origin: Literal["baseline", "duration", "user"] = "baseline"
    shareable: bool = True


class FamilyReadinessMilestone(BaseModel):
    milestone_id: str
    label: str
    title: str
    target_date: date


class FamilyReadinessContact(BaseModel):
    contact_id: str
    role: str
    organization: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    source_url: str | None = None
    last_verified_at: datetime | None = None
    shareable: bool = True


class FamilyReadinessGlossaryEntry(BaseModel):
    term: str
    expansion: str
    plain_language: str
    shareable: bool = True


class FamilyReadinessEventCreateRequest(BaseModel):
    user_key: str
    title: str = Field(min_length=1, max_length=200)
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand | None = None
    is_demo: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> "FamilyReadinessEventCreateRequest":
        if self.approximate_start and self.approximate_end and self.approximate_end < self.approximate_start:
            raise ValueError("approximate_end must be on or after approximate_start.")
        return self


class FamilyReadinessEventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand | None = None
    status: ReadinessEventStatus | None = None
    private_notes: str | None = Field(default=None, max_length=4000)


class FamilyReadinessItemCreateRequest(BaseModel):
    category: ReadinessItemCategory
    task: str = Field(min_length=1, max_length=240)
    plain_language: str = Field(min_length=1, max_length=500)
    responsible_label: str = Field(default="", max_length=120)
    target_date: date | None = None
    notes: str = Field(default="", max_length=2000)
    shareable: bool = True


class FamilyReadinessItemUpdateRequest(BaseModel):
    status: ReadinessItemStatus | None = None
    responsible_label: str | None = Field(default=None, max_length=120)
    target_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    shareable: bool | None = None


class FamilyReadinessItemOrderRequest(BaseModel):
    item_ids: list[str] = Field(min_length=1)


class FamilyReadinessContactUpsertRequest(BaseModel):
    contact_id: str | None = None
    role: str = Field(min_length=1, max_length=120)
    organization: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=1000)
    source_url: str | None = None
    shareable: bool = True


class FamilyReadinessGlossaryUpsertRequest(BaseModel):
    term: str = Field(min_length=1, max_length=80)
    expansion: str = Field(min_length=1, max_length=160)
    plain_language: str = Field(min_length=1, max_length=500)
    shareable: bool = True


class FamilyReadinessMilestoneUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    target_date: date | None = None


class FamilyReadinessEvent(BaseModel):
    event_id: str
    user_key: str
    title: str
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand
    status: ReadinessEventStatus = ReadinessEventStatus.planning
    items: list[FamilyReadinessChecklistItem] = Field(default_factory=list)
    contacts: list[FamilyReadinessContact] = Field(default_factory=list)
    glossary: list[FamilyReadinessGlossaryEntry] = Field(default_factory=list)
    milestones: list[FamilyReadinessMilestone] = Field(default_factory=list)
    private_notes: str = ""
    is_demo: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FamilyReadinessEventListResponse(BaseModel):
    total_events: int
    records: list[FamilyReadinessEvent] = Field(default_factory=list)


class FamilyReadinessSummaryRequest(BaseModel):
    user_key: str
