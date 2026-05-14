from enum import StrEnum

from pydantic import BaseModel, Field


class TrainingScenarioType(StrEnum):
    field_exercise = "field_exercise"
    range = "range"
    staff_drill = "staff_drill"
    pme = "pme"
    civil_support = "civil_support"
    annual_training = "annual_training"


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
