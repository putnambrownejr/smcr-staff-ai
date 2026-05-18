from pydantic import BaseModel, Field

from app.schemas.staff import StaffEchelon
from app.schemas.staff_products import StaffProductDraftResponse


class StaffSectionUpdate(BaseModel):
    section: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    changes_since_last: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    open_issues: list[str] = Field(default_factory=list)
    support_requests: list[str] = Field(default_factory=list)
    decisions_needed: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_24_72: list[str] = Field(default_factory=list)
    adjacent_section_asks: list[str] = Field(default_factory=list)


class RunningEstimateRequest(BaseModel):
    title: str = Field(min_length=1)
    supported_unit: str = Field(min_length=1)
    supported_echelon: StaffEchelon = StaffEchelon.company
    mission_or_training_goal: str = Field(min_length=1)
    timeframe: str | None = None
    commander_priorities: list[str] = Field(default_factory=list)
    higher_guidance: list[str] = Field(default_factory=list)
    met_tasks: list[str] = Field(default_factory=list)
    metl_focus: list[str] = Field(default_factory=list)
    section_updates: list[StaffSectionUpdate] = Field(default_factory=list)
    training_only: bool = True


class RunningEstimateItem(BaseModel):
    section: str
    current_situation: list[str] = Field(default_factory=list)
    changes_since_last: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    supportability: list[str] = Field(default_factory=list)
    decisions_needed: list[str] = Field(default_factory=list)
    next_24_72: list[str] = Field(default_factory=list)
    asks_of_adjacent_sections: list[str] = Field(default_factory=list)


class RunningEstimateResponse(BaseModel):
    title: str
    supported_unit: str
    running_estimates: list[RunningEstimateItem] = Field(default_factory=list)
    command_summary: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CubResponse(BaseModel):
    title: str
    command_snapshot: list[str] = Field(default_factory=list)
    running_estimates: list[RunningEstimateItem] = Field(default_factory=list)
    cross_staff_friction: list[str] = Field(default_factory=list)
    commander_decisions: list[str] = Field(default_factory=list)
    due_outs: list[str] = Field(default_factory=list)
    update_brief: StaffProductDraftResponse
    warnings: list[str] = Field(default_factory=list)


class CpbResponse(BaseModel):
    title: str
    command_frame: list[str] = Field(default_factory=list)
    running_estimates: list[RunningEstimateItem] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    decision_points: list[str] = Field(default_factory=list)
    branches_and_sequels: list[str] = Field(default_factory=list)
    command_brief: StaffProductDraftResponse
    warnings: list[str] = Field(default_factory=list)


class StaffUpdateCycleResponse(BaseModel):
    title: str
    running_estimate: RunningEstimateResponse
    cub: CubResponse
    cpb: CpbResponse
    warnings: list[str] = Field(default_factory=list)
