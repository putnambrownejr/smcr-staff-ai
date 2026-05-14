from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.personnel import CorrespondenceConversionRequest
from app.schemas.poam import PoamRequest
from app.schemas.tdg import TdgGenerationRequest
from app.schemas.training import AnnualTrainingPlanRequest, RangePackageRequest


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


class ActionLinkType(StrEnum):
    local_context = "local_context"
    documentation_update = "documentation_update"
    url = "url"


class ActionLinkRecord(BaseModel):
    link_id: str
    link_type: ActionLinkType
    label: str
    target_id: str | None = None
    url: str | None = None
    notes: str | None = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


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
    links: list[ActionLinkRecord] = Field(default_factory=list)
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


class ActionLinkRequest(BaseModel):
    link_type: ActionLinkType
    label: str
    target_id: str | None = None
    url: str | None = None
    notes: str | None = None


class ActionPromoteItemRequest(BaseModel):
    text: str
    owner: str | None = None
    category: ActionCategory | None = None
    priority: ActionPriority | None = None
    suspense_date: date | None = None
    source_ref: str | None = None
    notes: str | None = None
    links: list[ActionLinkRequest] = Field(default_factory=list)


class ActionPromoteRequest(BaseModel):
    user_key: str | None = None
    items: list[ActionPromoteItemRequest]
    default_owner: str | None = None
    default_category: ActionCategory = ActionCategory.poam
    default_priority: ActionPriority = ActionPriority.medium
    source_ref: str | None = None
    shared_links: list[ActionLinkRequest] = Field(default_factory=list)


class ActionPromoteResponse(BaseModel):
    tracked: list[ActionRecord]
    summary_lines: list[str] = Field(default_factory=list)
    message: str


class ActionBundleTrackRequest(BaseModel):
    user_key: str | None = None
    owner: str | None = None


class ActionBundleTrackResponse(BaseModel):
    source_title: str
    tracked: list[ActionRecord]
    summary_lines: list[str] = Field(default_factory=list)
    message: str


class AnnualTrainingActionBundleRequest(BaseModel):
    plan: AnnualTrainingPlanRequest
    options: ActionBundleTrackRequest = Field(default_factory=ActionBundleTrackRequest)


class CorrespondenceActionBundleRequest(BaseModel):
    draft: CorrespondenceConversionRequest
    options: ActionBundleTrackRequest = Field(default_factory=ActionBundleTrackRequest)


class RangePackageActionBundleRequest(BaseModel):
    package: RangePackageRequest
    options: ActionBundleTrackRequest = Field(default_factory=ActionBundleTrackRequest)


class TdgActionBundleRequest(BaseModel):
    tdg: TdgGenerationRequest
    options: ActionBundleTrackRequest = Field(default_factory=ActionBundleTrackRequest)


class PoamActionBundleRequest(BaseModel):
    poam: PoamRequest
    options: ActionBundleTrackRequest = Field(default_factory=ActionBundleTrackRequest)


class ActionFollowUpRequest(BaseModel):
    action_ids: list[str] = Field(default_factory=list)
    notes: str
    status: ActionStatus | None = None


class ActionFollowUpResult(BaseModel):
    action_id: str
    title: str
    status: ActionStatus
    notes: str | None = None


class ActionFollowUpResponse(BaseModel):
    updated: list[ActionFollowUpResult] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)
    message: str
