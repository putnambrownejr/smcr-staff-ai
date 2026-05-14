from enum import StrEnum

from pydantic import BaseModel, Field


class TrainingScenarioType(StrEnum):
    field_exercise = "field_exercise"
    range = "range"
    staff_drill = "staff_drill"
    pme = "pme"
    civil_support = "civil_support"


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
