from datetime import date, time

from pydantic import BaseModel, Field


class DrillKeyEvent(BaseModel):
    title: str
    event_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    uniform: str | None = None
    due_outs: list[str] = Field(default_factory=list)
    source_context_id: str | None = None
    confidence: str = "low"
    classification_label: str = "UNCLASSIFIED"
    notes: str | None = None
    warnings: list[str] = Field(default_factory=list)


class DrillPrepPlanRequest(BaseModel):
    drill_date: date
    unit_id: str | None = None
    include_travel_tasks: bool = True
    key_events: list[DrillKeyEvent] = Field(default_factory=list)
    context_ids: list[str] = Field(default_factory=list)


class PrepTask(BaseModel):
    title: str
    due_offset_days: int
    due_date: date
    category: str
    advisory: bool = True


class DrillPrepPlanResponse(BaseModel):
    id: str
    drill_date: date
    tasks: list[PrepTask]
    key_events: list[DrillKeyEvent] = Field(default_factory=list)
    context_ids: list[str] = Field(default_factory=list)
    local_context_used: bool = False
    warnings: list[str] = Field(default_factory=list)


class HandoffReminderPlanRequest(BaseModel):
    include_travel_tasks: bool = True
    only_future_drills: bool = True


class HandoffReminderPlanResponse(BaseModel):
    user_key: str
    generated_plan_ids: list[str] = Field(default_factory=list)
    plans: list[DrillPrepPlanResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
