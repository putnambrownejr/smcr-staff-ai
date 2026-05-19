from pydantic import BaseModel, Field

from app.schemas.planning import PlanningApproachAssessment
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
    user_key: str | None = None
    title: str = Field(min_length=1)
    supported_unit: str = Field(min_length=1)
    supported_echelon: StaffEchelon = StaffEchelon.company
    event_type: str = "training_event"
    mission_or_training_goal: str = Field(min_length=1)
    timeframe: str | None = None
    time_available: str | None = None
    commander_priorities: list[str] = Field(default_factory=list)
    higher_guidance: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    coordinating_sections: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    partner_types: list[str] = Field(default_factory=list)
    civil_considerations: list[str] = Field(default_factory=list)
    met_tasks: list[str] = Field(default_factory=list)
    metl_focus: list[str] = Field(default_factory=list)
    section_updates: list[StaffSectionUpdate] = Field(default_factory=list)
    training_only: bool = True


class AssistedSectionEstimateRequest(RunningEstimateRequest):
    focus_sections: list[str] = Field(default_factory=list)


class MissionAnalysisResponse(BaseModel):
    title: str
    supported_unit: str
    mission_statement: str
    command_frame: list[str] = Field(default_factory=list)
    specified_tasks: list[str] = Field(default_factory=list)
    implied_tasks: list[str] = Field(default_factory=list)
    essential_tasks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    information_requirements: list[str] = Field(default_factory=list)
    staff_estimate_requirements: list[str] = Field(default_factory=list)
    commander_decisions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


class PlanningCellResponse(BaseModel):
    title: str
    planning_approach: PlanningApproachAssessment
    mission_analysis: MissionAnalysisResponse
    update_cycle: StaffUpdateCycleResponse
    assumption_log: list[str] = Field(default_factory=list)
    commander_decision_log: list[str] = Field(default_factory=list)
    due_out_board: list[str] = Field(default_factory=list)
    red_team_focus: list[str] = Field(default_factory=list)
    next_opt_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LonePlannerResponse(BaseModel):
    title: str
    posture: str
    walk_in_brief: list[str] = Field(default_factory=list)
    likely_blind_spots: list[str] = Field(default_factory=list)
    missing_section_questions: list[str] = Field(default_factory=list)
    cross_lane_asks: list[str] = Field(default_factory=list)
    recommended_products: list[str] = Field(default_factory=list)
    immediate_actions: list[str] = Field(default_factory=list)
    planning_cell: PlanningCellResponse
    warnings: list[str] = Field(default_factory=list)


class AssistedSectionEstimateItem(BaseModel):
    section: str
    section_status: str
    known_inputs: list[str] = Field(default_factory=list)
    likely_questions: list[str] = Field(default_factory=list)
    likely_support_facts: list[str] = Field(default_factory=list)
    likely_coordination: list[str] = Field(default_factory=list)
    draft_estimate_lines: list[str] = Field(default_factory=list)
    confidence_note: str


class AssistedSectionEstimatesResponse(BaseModel):
    title: str
    posture: str
    focus_sections: list[str] = Field(default_factory=list)
    section_estimates: list[AssistedSectionEstimateItem] = Field(default_factory=list)
    cross_lane_risks: list[str] = Field(default_factory=list)
    xo_walk_in_lines: list[str] = Field(default_factory=list)
    recommended_products: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
