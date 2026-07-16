from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.schemas.civil_network import CivilNetworkSnapshot


class StaffEchelon(StrEnum):
    platoon = "platoon"
    company = "company"
    battalion = "battalion"
    regiment_meu_wing = "regiment_meu_wing"
    division_group = "division_group"


class MagtfLens(StrEnum):
    ce_c2 = "ce_c2"
    gce = "gce"
    ace = "ace"
    lce = "lce"


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
    phase: str = "section_estimate"
    magtf_lenses: list[MagtfLens] = Field(default_factory=list)
    answer: str
    estimate: list[str] = Field(default_factory=list)
    critical_questions: list[str] = Field(default_factory=list)
    assumptions_to_test: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    critique_points: list[str] = Field(default_factory=list)
    cross_staff_risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    recommended_products: list[str] = Field(default_factory=list)
    coordination_notes: list[str] = Field(default_factory=list)
    branch_sequel_prompts: list[str] = Field(default_factory=list)
    commander_decisions: list[str] = Field(default_factory=list)
    mcpp_step: str | None = None
    mcpp_discipline: str | None = None
    pme_grounding: str | None = None
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
    pace_matrix: list[dict[str, str]] = Field(default_factory=list)
    radio_guard_chart: list[dict[str, str]] = Field(default_factory=list)
    comm_plan_outline: list[str] = Field(default_factory=list)
    information_management_checks: list[str] = Field(default_factory=list)
    support_requirements: list[str] = Field(default_factory=list)
    permissions_and_dependencies: list[str] = Field(default_factory=list)
    reserve_friction_points: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class XoSyncRequest(BaseModel):
    title: str
    supported_event: str
    command_focus: str
    audience: str | None = None
    coordinating_sections: list[str] = Field(default_factory=list)
    critical_decisions: list[str] = Field(default_factory=list)
    due_outs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True


class XoSyncResponse(BaseModel):
    title: str
    command_sync_frame: list[str] = Field(default_factory=list)
    synchronization_matrix: list[str] = Field(default_factory=list)
    decision_support_matrix: list[str] = Field(default_factory=list)
    due_out_tracker: list[str] = Field(default_factory=list)
    command_review_points: list[str] = Field(default_factory=list)
    friction_checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CommandCellRequest(BaseModel):
    title: str
    supported_event: str
    command_focus: str
    audience: str | None = None
    coordinating_sections: list[str] = Field(default_factory=list)
    critical_decisions: list[str] = Field(default_factory=list)
    due_outs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True


class CommandCellResponse(BaseModel):
    title: str
    command_cell_frame: list[str] = Field(default_factory=list)
    chief_focus_board: list[str] = Field(default_factory=list)
    battle_captain_watchboard: list[str] = Field(default_factory=list)
    command_update_lines: list[str] = Field(default_factory=list)
    turnover_handoff_notes: list[str] = Field(default_factory=list)
    ccir_and_decision_triggers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class S1ReadinessRequest(BaseModel):
    title: str
    supported_event: str
    audience: str | None = None
    admin_priorities: list[str] = Field(default_factory=list)
    admin_risks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    travel_required: bool = True
    training_only: bool = True


class S1ReadinessResponse(BaseModel):
    title: str
    readiness_estimate: list[str] = Field(default_factory=list)
    admin_status_board: list[str] = Field(default_factory=list)
    admin_task_tracker: list[str] = Field(default_factory=list)
    routing_matrix: list[str] = Field(default_factory=list)
    pre_drill_admin_readiness_check: list[str] = Field(default_factory=list)
    continuity_notes: list[str] = Field(default_factory=list)
    critical_suspenses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SafetyPlanningRequest(BaseModel):
    title: str
    supported_event: str
    audience: str | None = None
    hazards: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    risk_decisions: list[str] = Field(default_factory=list)
    live_fire: bool = False
    vehicle_ops: bool = False
    overnight: bool = False
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True


class SafetyPlanningResponse(BaseModel):
    title: str
    orm_framework: list[str] = Field(default_factory=list)
    no_go_criteria: list[str] = Field(default_factory=list)
    residual_risk_decisions: list[str] = Field(default_factory=list)
    rehearsal_checks: list[str] = Field(default_factory=list)
    stop_training_triggers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SelExecutionRequest(BaseModel):
    title: str
    supported_event: str
    audience: str | None = None
    accountability_risks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    formal_event: bool = False
    overnight: bool = False
    training_only: bool = True


class SelExecutionResponse(BaseModel):
    title: str
    troop_flow_plan: list[str] = Field(default_factory=list)
    troop_flow_checklist: list[str] = Field(default_factory=list)
    accountability_scheme: list[str] = Field(default_factory=list)
    formation_transition_matrix: list[str] = Field(default_factory=list)
    leader_touchpoints: list[str] = Field(default_factory=list)
    leader_touchpoint_plan: list[str] = Field(default_factory=list)
    standards_checks: list[str] = Field(default_factory=list)
    marine_welfare_checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class G9OperatingContext(StrEnum):
    domestic_support = "domestic_support"
    overseas_partner = "overseas_partner"


class G9SourceItem(BaseModel):
    title: str = Field(min_length=1)
    url: str | None = None
    publisher: str | None = None
    retrieved_at: str | None = None
    claim: str | None = None
    source_type: str | None = None
    corroborated: bool = False

    @field_validator("retrieved_at")
    @classmethod
    def validate_retrieved_at(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            datetime.fromisoformat(value)
        except ValueError as error:
            msg = "retrieved_at must be an ISO-8601 date or datetime."
            raise ValueError(msg) from error
        return value


class G9InfrastructureSystem(BaseModel):
    system: str = Field(min_length=1)
    condition_or_concern: str | None = None
    known_dependency: str | None = None
    source_label: str | None = None


class G9CulturalContextItem(BaseModel):
    documented_context: str = Field(min_length=1)
    source_label: str | None = None
    regional_variation: str | None = None
    planning_relevance: str | None = None


class G9EvidenceKind(StrEnum):
    reported_fact = "reported_fact"
    analytic_inference = "analytic_inference"
    planning_assumption = "planning_assumption"
    synthetic_exercise_content = "synthetic_exercise_content"


class G9EvidenceAssessment(BaseModel):
    kind: G9EvidenceKind
    statement: str
    source_label: str | None = None
    source_date: str | None = None
    confidence: str
    verification_note: str


class G9PlanningRequest(BaseModel):
    title: str
    supported_problem: str
    audience: str | None = None
    partner_types: list[str] = Field(default_factory=list)
    civil_considerations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    training_only: bool = True
    operating_context: G9OperatingContext | None = None
    source_items: list[G9SourceItem] = Field(default_factory=list)
    infrastructure_systems: list[G9InfrastructureSystem] = Field(default_factory=list)
    cultural_context_items: list[G9CulturalContextItem] = Field(default_factory=list)
    civil_network_snapshot: CivilNetworkSnapshot | None = None


class G9PlanningResponse(BaseModel):
    title: str
    civil_situation_frame: list[str] = Field(default_factory=list)
    partner_coordination: list[str] = Field(default_factory=list)
    information_requirements: list[str] = Field(default_factory=list)
    engagement_considerations: list[str] = Field(default_factory=list)
    continuity_and_transition: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    operating_context_frame: list[str] = Field(default_factory=list)
    infrastructure_dependency_assessment: list[str] = Field(default_factory=list)
    cultural_context_assessment: list[str] = Field(default_factory=list)
    evidence_and_assumptions: list[G9EvidenceAssessment] = Field(default_factory=list)
    civil_estimate_outline: list[str] = Field(default_factory=list)
    civil_network_assessment: list[str] = Field(default_factory=list)


class MedicalPlanningRequest(BaseModel):
    title: str
    supported_event: str
    medical_risk_context: list[str] = Field(default_factory=list)
    casualty_scenarios: list[str] = Field(default_factory=list)
    audience: str | None = None
    overnight: bool = False
    travel_required: bool = False
    training_only: bool = True


class MedicalPlanningResponse(BaseModel):
    title: str
    medical_support_estimate: list[str] = Field(default_factory=list)
    tccc_considerations: list[str] = Field(default_factory=list)
    tccc_knowledge_points: list[str] = Field(default_factory=list)
    nine_line_considerations: list[str] = Field(default_factory=list)
    casevac_plan_elements: list[str] = Field(default_factory=list)
    casevac_medevac_check: list[str] = Field(default_factory=list)
    casualty_collection_logic: list[str] = Field(default_factory=list)
    medical_decision_points: list[str] = Field(default_factory=list)
    medical_rehearsal_checks: list[str] = Field(default_factory=list)
    coordination_requirements: list[str] = Field(default_factory=list)
    coordination_trigger_list: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
