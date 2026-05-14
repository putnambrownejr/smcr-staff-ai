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
