from pydantic import BaseModel, ConfigDict, Field

from app.schemas.staff import (
    G9PlanningResponse,
    MedicalPlanningResponse,
    S2EstimateResponse,
    S6PlanResponse,
    StaffCouncilResponse,
)
from app.schemas.staff_products import StaffProductDraftResponse, StaffProductType
from app.schemas.training import S3PlanningResponse, S4PlanningResponse


class StaffPlanningPackageRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Reserve field training package",
                "event_type": "field_training",
                "mission_or_training_goal": "Build a one-day field event that improves staff and small-unit readiness.",
                "audience": "Civil affairs company",
                "timeframe": "Next drill weekend",
                "constraints": ["One field day", "Distributed Marines", "Travel required for some personnel"],
                "coordinating_sections": ["S-1", "S-4", "S-6", "Safety / ORM"],
                "support_requirements": ["Billeting", "Movement accountability", "Medical support"],
                "product_types": ["warno", "frago", "aar"],
                "training_only": True,
            }
        }
    )
    title: str = Field(min_length=1)
    event_type: str = "drill_weekend"
    mission_or_training_goal: str = Field(min_length=1)
    audience: str | None = None
    timeframe: str | None = None
    constraints: list[str] = Field(default_factory=list)
    coordinating_sections: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    partner_types: list[str] = Field(default_factory=list)
    civil_considerations: list[str] = Field(default_factory=list)
    medical_risk_context: list[str] = Field(default_factory=list)
    casualty_scenarios: list[str] = Field(default_factory=list)
    source_items: list[dict[str, str]] = Field(default_factory=list)
    intelligence_question: str | None = None
    c2_objective: str | None = None
    support_objective: str | None = None
    include_g9: bool | None = None
    product_types: list[StaffProductType] = Field(
        default_factory=lambda: [StaffProductType.warno, StaffProductType.frago, StaffProductType.aar]
    )
    preferred_format: str | None = None
    training_only: bool = True


class StaffPlanningPackageResponse(BaseModel):
    title: str
    summary: list[str] = Field(default_factory=list)
    recommended_course_of_action: list[str] = Field(default_factory=list)
    commander_decisions_now: list[str] = Field(default_factory=list)
    top_risks: list[str] = Field(default_factory=list)
    cuts_and_deferments: list[str] = Field(default_factory=list)
    execution_framework: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    s2_estimate: S2EstimateResponse | None = None
    s3_plan: S3PlanningResponse
    s4_plan: S4PlanningResponse
    s6_plan: S6PlanResponse
    medical_plan: MedicalPlanningResponse
    g9_plan: G9PlanningResponse | None = None
    battalion_staff_review: StaffCouncilResponse
    general_staff_review: StaffCouncilResponse | None = None
    xo_vet: StaffCouncilResponse
    product_package: list[StaffProductDraftResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
