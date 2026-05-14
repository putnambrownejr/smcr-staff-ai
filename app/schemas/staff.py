from enum import StrEnum

from pydantic import BaseModel, Field


class StaffEchelon(StrEnum):
    company = "company"
    battalion = "battalion"
    division_group = "division_group"


class StaffRoleMetadata(BaseModel):
    agent_id: str
    echelon: StaffEchelon
    role: str
    name: str
    maturity: str
    scope: str
    osint_enabled: bool = False


class StaffCouncilRequest(BaseModel):
    question: str = Field(min_length=1)
    echelon: StaffEchelon
    roles: list[str] = Field(default_factory=list)
    context: dict[str, object] = Field(default_factory=dict)


class StaffRoundRobinRequest(BaseModel):
    question: str = Field(min_length=1)
    echelons: list[StaffEchelon] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    context: dict[str, object] = Field(default_factory=dict)


class StaffPerspective(BaseModel):
    agent_id: str
    role: str
    echelon: StaffEchelon
    answer: str
    concerns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[dict[str, object]] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: str = "low"


class StaffCouncilResponse(BaseModel):
    question: str
    echelon: StaffEchelon
    perspectives: list[StaffPerspective]
    synthesis: str
    roles_requested: list[str] = Field(default_factory=list)
    roles_run: list[str] = Field(default_factory=list)
    roles_missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StaffRoundRobinResponse(BaseModel):
    question: str
    phases: list[str]
    councils: list[StaffCouncilResponse]
    synthesis: str
    warnings: list[str] = Field(default_factory=list)


class S2EstimateRequest(BaseModel):
    title: str
    question: str
    source_items: list[dict[str, str]] = Field(default_factory=list)
    audience: str | None = None
    timeframe: str | None = None
    planning_only: bool = True


class S2EstimateResponse(BaseModel):
    title: str
    summary_assessment: list[str] = Field(default_factory=list)
    assessed_claims: list[str] = Field(default_factory=list)
    collection_gaps: list[str] = Field(default_factory=list)
    command_considerations: list[str] = Field(default_factory=list)
    source_caveats: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class S6PlanRequest(BaseModel):
    title: str
    supported_event: str
    c2_objective: str
    audience: str | None = None
    distributed_personnel: bool = True
    constraints: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    training_only: bool = True


class S6PlanResponse(BaseModel):
    title: str
    c2_support_estimate: list[str] = Field(default_factory=list)
    pace_considerations: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    permissions_and_dependencies: list[str] = Field(default_factory=list)
    reserve_friction_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
