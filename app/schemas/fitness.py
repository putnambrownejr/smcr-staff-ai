from enum import StrEnum

from pydantic import BaseModel, Field


class FitnessObjective(StrEnum):
    general = "general fitness"
    pft = "PFT preparation"
    cft = "CFT preparation"
    strength = "strength"
    endurance = "endurance"
    mobility = "mobility/recovery"


class UnitPtPlanRequest(BaseModel):
    participant_count: int = Field(ge=5, le=50)
    objective: FitnessObjective = FitnessObjective.general
    duration_minutes: int = Field(default=60, ge=20, le=120)
    location: str = Field(default="unit training area", max_length=160)
    equipment: list[str] = Field(default_factory=list, max_length=20)
    ability_notes: str = Field(default="mixed ability", max_length=500)
    limitations: list[str] = Field(default_factory=list, max_length=20)
    weather_notes: str = Field(default="check current conditions", max_length=240)
    include_cadence: bool = True
    cadence_preference: str | None = Field(default=None, max_length=120)


class PtBlock(BaseModel):
    name: str
    minutes: int
    instructions: list[str] = Field(default_factory=list)
    scaling: list[str] = Field(default_factory=list)


class StaffPtReview(BaseModel):
    role: str
    findings: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class OrmHazard(BaseModel):
    hazard: str
    initial_risk: str
    controls: list[str]
    residual_risk: str
    owner: str
    stop_trigger: str


class OrmMatrix(BaseModel):
    hazards: list[OrmHazard]
    acceptance_note: str = (
        "Planning aid only. The appropriate commander/supervisor accepts residual risk under current policy."
    )


class UnitPtPlan(BaseModel):
    participant_count: int
    scaling_band: str
    objective: FitnessObjective
    duration_minutes: int
    organization: list[str]
    blocks: list[PtBlock]
    cadence: str | None = None
    staff_reviews: list[StaffPtReview]
    orm: OrmMatrix
    warnings: list[str]
    sources: list[str]
    footer: str = "DRAFT — Verify all references against current official sources before acting."
