from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import Confidence, StructuredCitation


class StaffProductType(StrEnum):
    opord = "opord"
    warno = "warno"
    frago = "frago"
    conop = "conop"
    sitrep = "sitrep"
    air_support_estimate = "air_support_estimate"
    air_ground_coordination_matrix = "air_ground_coordination_matrix"
    aviation_supportability_matrix = "aviation_supportability_matrix"
    public_affairs_plan = "public_affairs_plan"
    security_annex = "security_annex"
    visitor_control_checklist = "visitor_control_checklist"
    traffic_parking_control_plan = "traffic_parking_control_plan"
    orm_worksheet = "orm_worksheet"
    no_go_criteria = "no_go_criteria"
    residual_risk_decision_note = "residual_risk_decision_note"
    rehearsal_safety_brief = "rehearsal_safety_brief"
    admin_estimate = "admin_estimate"
    admin_task_tracker = "admin_task_tracker"
    routing_matrix = "routing_matrix"
    pre_drill_admin_readiness_check = "pre_drill_admin_readiness_check"
    troop_flow_checklist = "troop_flow_checklist"
    formation_transition_matrix = "formation_transition_matrix"
    leader_touchpoint_plan = "leader_touchpoint_plan"
    resource_estimate = "resource_estimate"
    inspection_readiness_plan = "inspection_readiness_plan"
    running_estimate = "running_estimate"
    synchronization_matrix = "synchronization_matrix"
    decision_support_matrix = "decision_support_matrix"
    due_out_tracker = "due_out_tracker"
    collection_matrix = "collection_matrix"
    sustainment_matrix = "sustainment_matrix"
    movement_table = "movement_table"
    medical_estimate = "medical_estimate"
    casevac_quick_card = "casevac_quick_card"
    religious_support_plan = "religious_support_plan"
    rmt_support_matrix = "rmt_support_matrix"
    morale_welfare_estimate = "morale_welfare_estimate"
    road_to_war_brief = "road_to_war_brief"
    aar = "aar"
    ipb = "ipb"
    decision_brief = "decision_brief"
    command_update_brief = "command_update_brief"
    naval_letter = "naval_letter"
    memorandum = "memorandum"
    endorsement = "endorsement"


class StaffProductDraftRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_type": "opord",
                "topic": "Training-only drill weekend field exercise",
                "audience": "Company staff",
                "facts": ["Timeline is tentative", "Scenario is fictional and training-only"],
                "training_or_fictional": True,
            }
        }
    )
    product_type: StaffProductType
    topic: str = Field(min_length=1)
    audience: str | None = None
    echelon: str | None = None
    preferred_format: str | None = None
    facts: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    template_ids: list[str] = Field(default_factory=list)
    training_or_fictional: bool = True
    include_review_checklist: bool = True


class StaffProductSection(BaseModel):
    heading: str
    prompts: list[str]


class StaffProductDraftResponse(BaseModel):
    product_type: StaffProductType
    title: str
    sections: list[StaffProductSection]
    applied_templates: list[str] = Field(default_factory=list)
    formatting_notes: list[str] = Field(default_factory=list)
    review_checklist: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
