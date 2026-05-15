from enum import StrEnum

from pydantic import BaseModel, Field


class TrainingScenarioType(StrEnum):
    field_exercise = "field_exercise"
    range = "range"
    staff_drill = "staff_drill"
    pme = "pme"
    civil_support = "civil_support"
    annual_training = "annual_training"


class TrainingCaseStudyRequest(BaseModel):
    title: str
    framing_question: str
    training_objective: str
    audience: str | None = None
    source_items: list[dict[str, str]] = Field(default_factory=list)
    current_event_context: list[str] = Field(default_factory=list)
    met_tasks: list[str] = Field(default_factory=list)
    metl_focus: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True


class TrainingCaseStudyResponse(BaseModel):
    title: str
    situation_frame: list[str] = Field(default_factory=list)
    case_summary: list[str] = Field(default_factory=list)
    key_observations: list[str] = Field(default_factory=list)
    s2_estimate: list[str] = Field(default_factory=list)
    met_alignment: list[str] = Field(default_factory=list)
    conop_implications: list[str] = Field(default_factory=list)
    discussion_questions: list[str] = Field(default_factory=list)
    aar_focus: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TrainingScenarioRequest(BaseModel):
    scenario_type: TrainingScenarioType
    title: str
    training_objective: str
    audience: str | None = None
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True


class TrainingScenarioResponse(BaseModel):
    title: str
    scenario_type: TrainingScenarioType
    concept: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    admin_requirements: list[str] = Field(default_factory=list)
    orm_considerations: list[str] = Field(default_factory=list)
    aar_prompts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RangeSafetyRequest(BaseModel):
    event_name: str
    weapon_systems: list[str] = Field(default_factory=list)
    ammunition: list[str] = Field(default_factory=list)
    audience: str | None = None
    training_only: bool = True


class RangeSafetyResponse(BaseModel):
    title: str
    required_roles: list[str] = Field(default_factory=list)
    required_admin: list[str] = Field(default_factory=list)
    orm_controls: list[str] = Field(default_factory=list)
    aar_prompts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AnnualTrainingPlanRequest(BaseModel):
    unit_name: str
    training_objectives: list[str] = Field(default_factory=list)
    date_window: str | None = None
    audience: str | None = None
    travel_required: bool = True
    distributed_personnel: bool = True
    constraints: list[str] = Field(default_factory=list)


class AnnualTrainingPlanResponse(BaseModel):
    title: str
    planning_phases: list[str] = Field(default_factory=list)
    admin_due_outs: list[str] = Field(default_factory=list)
    logistics_considerations: list[str] = Field(default_factory=list)
    readiness_checks: list[str] = Field(default_factory=list)
    coordination_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RangePackageRequest(BaseModel):
    event_name: str
    unit_name: str | None = None
    weapon_systems: list[str] = Field(default_factory=list)
    ammunition: list[str] = Field(default_factory=list)
    audience: str | None = None
    range_type: str | None = None
    overnight: bool = False
    travel_required: bool = False


class RangePackageResponse(BaseModel):
    title: str
    packet_components: list[str] = Field(default_factory=list)
    roles_and_responsibilities: list[str] = Field(default_factory=list)
    safety_controls: list[str] = Field(default_factory=list)
    medevac_and_comm_checks: list[str] = Field(default_factory=list)
    follow_up_requirements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class S3SubordinateUnitInput(BaseModel):
    unit_name: str
    relationship: str = "subordinate"
    purpose: str | None = None
    resource_bias: list[str] = Field(default_factory=list)


class S3SubordinatePromptPacket(BaseModel):
    unit_name: str
    relationship: str
    task: str
    purpose: str
    end_state: str
    resource_prompts: list[str] = Field(default_factory=list)
    planning_prompts: list[str] = Field(default_factory=list)
    reporting_requirements: list[str] = Field(default_factory=list)


class S3PlanningRequest(BaseModel):
    title: str
    mission_or_training_goal: str
    event_type: str = "drill_weekend"
    audience: str | None = None
    timeframe: str | None = None
    primary_scenario_input: str | None = None
    secondary_scenario_input: str | None = None
    current_event_context: list[str] = Field(default_factory=list)
    source_items: list[dict[str, str]] = Field(default_factory=list)
    met_tasks: list[str] = Field(default_factory=list)
    metl_focus: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    coordinating_sections: list[str] = Field(default_factory=list)
    subordinate_units: list[S3SubordinateUnitInput] = Field(default_factory=list)
    training_only: bool = True


class S3PlanningResponse(BaseModel):
    title: str
    mission_analysis: list[str] = Field(default_factory=list)
    scenario_frame: list[str] = Field(default_factory=list)
    scenario_escalation: list[str] = Field(default_factory=list)
    injects: list[str] = Field(default_factory=list)
    met_alignment: list[str] = Field(default_factory=list)
    critical_tasks: list[str] = Field(default_factory=list)
    coordination_matrix: list[str] = Field(default_factory=list)
    battle_rhythm: list[str] = Field(default_factory=list)
    command_decision_points: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)
    subordinate_prompt_packets: list[S3SubordinatePromptPacket] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    reserve_friction_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class S4PlanningRequest(BaseModel):
    title: str
    supported_event: str
    support_objective: str
    audience: str | None = None
    travel_required: bool = True
    overnight: bool = False
    distributed_personnel: bool = True
    constraints: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)


class S4PlanningResponse(BaseModel):
    title: str
    support_estimate: list[str] = Field(default_factory=list)
    critical_support_requirements: list[str] = Field(default_factory=list)
    movement_and_billeting: list[str] = Field(default_factory=list)
    sustainment_checks: list[str] = Field(default_factory=list)
    coordination_points: list[str] = Field(default_factory=list)
    reserve_friction_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
