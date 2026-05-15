from pydantic import BaseModel, ConfigDict, Field

from app.schemas.staff import (
    G9PlanningResponse,
    MedicalPlanningResponse,
    S2EstimateResponse,
    S6PlanResponse,
    StaffCouncilResponse,
    StaffEchelon,
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


class SubordinateUnitInput(BaseModel):
    unit_name: str = Field(min_length=1)
    unit_type: str | None = None
    relationship: str = "subordinate"
    purpose: str | None = None
    planning_requirements: list[str] = Field(default_factory=list)


class MetAlignmentItem(BaseModel):
    task_name: str
    alignment_type: str
    why_it_matters: str
    assessment_focus: str


class UnitRelationshipFrame(BaseModel):
    unit_name: str
    relationship: str
    task_focus: list[str] = Field(default_factory=list)
    support_dependencies: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)


class GuidanceExtraction(BaseModel):
    commander_intent: list[str] = Field(default_factory=list)
    directed_tasks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    coordinating_instructions: list[str] = Field(default_factory=list)
    command_relationship_notes: list[str] = Field(default_factory=list)
    assumptions_to_confirm: list[str] = Field(default_factory=list)


class SubordinateConopPacket(BaseModel):
    unit_name: str
    relationship: str
    task_statement: str
    purpose: str
    concept_focus: list[str] = Field(default_factory=list)
    command_and_support_relationships: list[str] = Field(default_factory=list)
    required_reports: list[str] = Field(default_factory=list)
    required_support_requests: list[str] = Field(default_factory=list)
    aar_focus: list[str] = Field(default_factory=list)


class FragoToConopRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Company field training refinement",
                "supported_echelon": "company",
                "higher_headquarters": "Battalion",
                "supported_unit": "Civil affairs company",
                "event_type": "field_training",
                "mission_or_training_goal": "Refine a company training scenario into an initial CONOP.",
                "higher_guidance": [
                    "Battalion FRAGO directs one-day field event.",
                    "Company will provide subordinate concept and support estimates."
                ],
                "s3_inputs": ["Need MET/METL alignment and staff synchronization."],
                "g9_inputs": ["Civil considerations should stay generic and training-only."],
                "subordinate_units": [
                    {"unit_name": "Detachment A", "relationship": "subordinate", "purpose": "Primary field lane"}
                ],
                "met_tasks": ["Conduct mission analysis"],
                "metl_focus": ["Plan and coordinate training"],
                "training_only": True,
            }
        }
    )
    title: str = Field(min_length=1)
    supported_echelon: StaffEchelon = StaffEchelon.company
    higher_headquarters: str | None = None
    supported_unit: str = Field(min_length=1)
    event_type: str = "training_event"
    mission_or_training_goal: str = Field(min_length=1)
    raw_guidance_text: str | None = None
    higher_guidance: list[str] = Field(default_factory=list)
    frago_facts: list[str] = Field(default_factory=list)
    s3_inputs: list[str] = Field(default_factory=list)
    g9_inputs: list[str] = Field(default_factory=list)
    source_items: list[dict[str, str]] = Field(default_factory=list)
    intelligence_question: str | None = None
    subordinate_units: list[SubordinateUnitInput] = Field(default_factory=list)
    met_tasks: list[str] = Field(default_factory=list)
    metl_focus: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    coordinating_sections: list[str] = Field(default_factory=list)
    partner_types: list[str] = Field(default_factory=list)
    civil_considerations: list[str] = Field(default_factory=list)
    medical_risk_context: list[str] = Field(default_factory=list)
    casualty_scenarios: list[str] = Field(default_factory=list)
    timeframe: str | None = None
    preferred_format: str | None = None
    formal_event: bool = False
    training_only: bool = True


class FragoToConopResponse(BaseModel):
    title: str
    guidance_summary: list[str] = Field(default_factory=list)
    commander_focus: list[str] = Field(default_factory=list)
    parsed_guidance: GuidanceExtraction
    unit_relationship_framework: list[UnitRelationshipFrame] = Field(default_factory=list)
    subordinate_conop_packets: list[SubordinateConopPacket] = Field(default_factory=list)
    met_alignment: list[MetAlignmentItem] = Field(default_factory=list)
    initial_conop: StaffProductDraftResponse
    frago_draft: StaffProductDraftResponse
    aar_framework: StaffProductDraftResponse
    s2_estimate: S2EstimateResponse | None = None
    s3_plan: S3PlanningResponse
    s4_plan: S4PlanningResponse
    s6_plan: S6PlanResponse
    medical_plan: MedicalPlanningResponse
    g9_plan: G9PlanningResponse | None = None
    xo_sel_review: StaffCouncilResponse | None = None
    key_assumptions: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    det_follow_on_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
