from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ActionStatus(StrEnum):
    open = "open"
    in_progress = "in_progress"
    waiting = "waiting"
    blocked = "blocked"
    complete = "complete"
    archived = "archived"


class ActionPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ActionCategory(StrEnum):
    poam = "poam"
    admin = "admin"
    drill = "drill"
    training = "training"
    travel = "travel"
    fitrep = "fitrep"
    pme = "pme"
    documents = "documents"
    career = "career"
    readiness = "readiness"
    other = "other"


class ActionRecord(BaseModel):
    action_id: str
    user_key: str | None = None
    title: str
    description: str | None = None
    owner: str | None = None
    category: ActionCategory = ActionCategory.poam
    priority: ActionPriority = ActionPriority.medium
    status: ActionStatus = ActionStatus.open
    suspense_date: date | None = None
    source_ref: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ActionItemRequest(BaseModel):
    user_key: str | None = None
    title: str
    description: str | None = None
    owner: str | None = None
    category: ActionCategory = ActionCategory.poam
    priority: ActionPriority = ActionPriority.medium
    status: ActionStatus = ActionStatus.open
    suspense_date: date | None = None
    source_ref: str | None = None
    notes: str | None = None


class ActionTrackRequest(BaseModel):
    actions: list[ActionItemRequest]


class ActionTrackResponse(BaseModel):
    tracked: list[ActionRecord]
    message: str


class ActionUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    owner: str | None = None
    category: ActionCategory | None = None
    priority: ActionPriority | None = None
    status: ActionStatus | None = None
    suspense_date: date | None = None
    source_ref: str | None = None
    notes: str | None = None
