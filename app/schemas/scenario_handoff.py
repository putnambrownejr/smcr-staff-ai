"""Structured scenario output schemas for inter-agent handoffs.

Each agent role that supports scenario mode defines a Pydantic model here.
These models capture the structured fields from the text templates so that
downstream agents can ingest prior assessments programmatically.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import SourceSelection
from app.schemas.external_processing import ExternalProcessingApproval

# ---------------------------------------------------------------------------
# G-9 Civil Estimate
# ---------------------------------------------------------------------------


class StrictScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CivilSituation(StrictScenarioModel):
    area: str = ""
    population: str = ""
    infrastructure: str = ""
    governance: str = ""


class AscopeEntry(StrictScenarioModel):
    areas: str = ""
    structures: str = ""
    capabilities: str = ""
    organizations: str = ""
    people: str = ""
    events: str = ""


class InteragencyCoordination(StrictScenarioModel):
    embassy_country_team: str = ""
    dos_dhr: str = ""
    un_ocha: str = ""
    ngo_landscape: str = ""


class CmoRecommendations(StrictScenarioModel):
    priority_actions: list[str] = Field(default_factory=list)
    liaison_requirements: list[str] = Field(default_factory=list)
    civil_info_requirements: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class G9ScenarioOutput(StrictScenarioModel):
    role: str = "g9"
    civil_situation: CivilSituation = Field(default_factory=CivilSituation)
    ascope: AscopeEntry = Field(default_factory=AscopeEntry)
    interagency: InteragencyCoordination = Field(default_factory=InteragencyCoordination)
    impact_on_operations: list[str] = Field(default_factory=list)
    cmo_recommendations: CmoRecommendations = Field(default_factory=CmoRecommendations)


# ---------------------------------------------------------------------------
# S-2 Intelligence Estimate
# ---------------------------------------------------------------------------


class ThreatAssessment(StrictScenarioModel):
    threat_actors: list[str] = Field(default_factory=list)
    disposition_and_capabilities: str = ""
    most_likely_coa: str = ""
    most_dangerous_coa: str = ""
    historical_pattern: str = ""


class IntelGaps(StrictScenarioModel):
    unknown_items: list[str] = Field(default_factory=list)
    priority_intel_requirements: list[str] = Field(default_factory=list)
    recommended_collection: list[str] = Field(default_factory=list)


class S2ScenarioOutput(StrictScenarioModel):
    role: str = "s2"
    area_of_operations: str = ""
    key_terrain_weather: str = ""
    infrastructure_status: str = ""
    threat: ThreatAssessment = Field(default_factory=ThreatAssessment)
    civil_considerations: str = ""
    intel_gaps: IntelGaps = Field(default_factory=IntelGaps)
    bottom_line: str = ""
    key_assumptions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# S-4 Logistics Estimate
# ---------------------------------------------------------------------------


class SupportRequirements(StrictScenarioModel):
    class_i_rations: str = ""
    class_iii_fuel: str = ""
    class_v_ammo: str = ""
    class_viii_medical: str = ""
    transportation: str = ""


class S4ScenarioOutput(StrictScenarioModel):
    role: str = "s4"
    logistics_environment: str = ""
    support_requirements: SupportRequirements = Field(default_factory=SupportRequirements)
    supportability_assessment: list[str] = Field(default_factory=list)
    longest_lead_item: str = ""
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# S-6 Communications Assessment
# ---------------------------------------------------------------------------


class PacePlan(StrictScenarioModel):
    primary: str = ""
    alternate: str = ""
    contingency: str = ""
    emergency: str = ""


class S6ScenarioOutput(StrictScenarioModel):
    role: str = "s6"
    comms_environment: str = ""
    pace_plan: PacePlan = Field(default_factory=PacePlan)
    interoperability_issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Surgeon — Medical Estimate
# ---------------------------------------------------------------------------


class SurgeonScenarioOutput(StrictScenarioModel):
    role: str = "surgeon"
    medical_environment: str = ""
    casualty_estimate: str = ""
    casevac_medevac_plan: str = ""
    class_viii_and_medical_logistics: str = ""
    medical_readiness_actions: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# SJA — Legal Issue-Spotter
# ---------------------------------------------------------------------------


class SjaScenarioOutput(StrictScenarioModel):
    role: str = "sja"
    legal_framework: str = ""
    roe_ruf_considerations: str = ""
    issues_spotted: list[str] = Field(default_factory=list)
    pause_until_reviewed: list[str] = Field(default_factory=list)
    claims_and_investigation_boundaries: str = ""
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# PAO / COMMSTRAT — Public Affairs Posture
# ---------------------------------------------------------------------------


class PaoScenarioOutput(StrictScenarioModel):
    role: str = "pao"
    information_environment: str = ""
    public_posture: str = ""
    release_authority: str = ""
    themes_and_messages: list[str] = Field(default_factory=list)
    anticipated_queries: list[str] = Field(default_factory=list)
    opsec_risks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# XO — Staff Integration and Decision Support
# ---------------------------------------------------------------------------


class XoScenarioOutput(StrictScenarioModel):
    role: str = "xo"
    commander_decisions: list[str] = Field(default_factory=list)
    staff_integration_gaps: list[str] = Field(default_factory=list)
    decision_support_matrix: list[str] = Field(default_factory=list)
    due_outs: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# Generic staff perspective (any seat, any input) and round-table synthesis
# ---------------------------------------------------------------------------


class StaffPerspectiveOutput(StrictScenarioModel):
    """A seat's assessment of arbitrary input; `role` is bound per seat at runtime."""

    role: str = ""
    summary: str = ""
    key_concerns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    products_to_build: list[str] = Field(default_factory=list)
    questions_for_commander: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class RoundtableSynthesisOutput(StrictScenarioModel):
    role: str = "cos_synthesis"
    bottom_line: str = ""
    integrated_assessment: str = ""
    decisions_for_commander: list[str] = Field(default_factory=list)
    taskings_by_seat: list[str] = Field(default_factory=list)
    products_to_produce: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# OpsO / S-3 — Operations and Training Estimate
# ---------------------------------------------------------------------------


class OpsoScenarioOutput(StrictScenarioModel):
    role: str = "opso"
    mission_and_end_state: str = ""
    training_objectives_or_tasks: list[str] = Field(default_factory=list)
    concept_of_operations: str = ""
    critical_path_and_suspenses: list[str] = Field(default_factory=list)
    resource_requests: list[str] = Field(default_factory=list)
    synchronization_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Provost — Force Protection and Security Estimate
# ---------------------------------------------------------------------------


class ProvostScenarioOutput(StrictScenarioModel):
    role: str = "provost"
    threat_and_fpcon_read: str = ""
    access_control_plan: str = ""
    movement_and_traffic_control: str = ""
    security_coordination: list[str] = Field(default_factory=list)
    use_of_force_boundaries: str = ""
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# G-8 — Resource Estimate
# ---------------------------------------------------------------------------


class G8ScenarioOutput(StrictScenarioModel):
    role: str = "g8"
    funding_sources_and_authorities: str = ""
    cost_drivers: list[str] = Field(default_factory=list)
    unfunded_requirements: list[str] = Field(default_factory=list)
    fiscal_controls_and_risks: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    resourcing_decision_point: str = ""
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Planning Advisor — Mission Analysis Shell
# ---------------------------------------------------------------------------


class MissionAnalysis(StrictScenarioModel):
    higher_intent: str = ""
    restated_mission: str = ""


class TaskBreakdown(StrictScenarioModel):
    specified: list[str] = Field(default_factory=list)
    implied: list[str] = Field(default_factory=list)
    essential: list[str] = Field(default_factory=list)


class Constraints(StrictScenarioModel):
    must_do: list[str] = Field(default_factory=list)
    must_not_do: list[str] = Field(default_factory=list)


class PlanningScenarioOutput(StrictScenarioModel):
    role: str = "planning"
    tempo: str = ""
    mission_analysis: MissionAnalysis = Field(default_factory=MissionAnalysis)
    tasks: TaskBreakdown = Field(default_factory=TaskBreakdown)
    constraints: Constraints = Field(default_factory=Constraints)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    information_requirements: list[str] = Field(default_factory=list)
    planning_watchpoints: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Chief of Staff — Commander's Watch List
# ---------------------------------------------------------------------------


class StaffTasking(StrictScenarioModel):
    s2: str = ""
    s3: str = ""
    s4: str = ""
    s6: str = ""
    g9_cmo: str = ""
    pao: str = ""


class CoSScenarioOutput(StrictScenarioModel):
    role: str = "cos"
    immediate_actions: list[str] = Field(default_factory=list)
    staff_tasking: StaffTasking = Field(default_factory=StaffTasking)
    decision_points: list[str] = Field(default_factory=list)
    coordination_requirements: list[str] = Field(default_factory=list)
    risk_watch: list[str] = Field(default_factory=list)
    battle_rhythm: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Unit PT planning staff handoffs
# ---------------------------------------------------------------------------


class FitnessScenarioOutput(StrictScenarioModel):
    role: str = "fitness"
    objective: str = ""
    participant_count: int = 0
    organization: list[str] = Field(default_factory=list)
    training_blocks: list[str] = Field(default_factory=list)
    safety_warnings: list[str] = Field(default_factory=list)


class OpsPtScenarioOutput(StrictScenarioModel):
    role: str = "opso_pt"
    schedule_actions: list[str] = Field(default_factory=list)
    training_standard: str = ""
    cancellation_criteria: list[str] = Field(default_factory=list)


class SelPtScenarioOutput(StrictScenarioModel):
    role: str = "sel"
    accountability_actions: list[str] = Field(default_factory=list)
    standards_and_scaling: list[str] = Field(default_factory=list)


class OrmPtScenarioOutput(StrictScenarioModel):
    role: str = "orm"
    hazards: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    residual_risk_note: str = ""


# ---------------------------------------------------------------------------
# Area Study Builder
# ---------------------------------------------------------------------------


class AreaStudyScenarioOutput(StrictScenarioModel):
    """Public-source civil baseline passed to downstream planning specialists."""

    role: str = "area_study"
    operational_area: str = ""
    pmesii: dict[str, list[str]] = Field(default_factory=dict)
    ascope: AscopeEntry = Field(default_factory=AscopeEntry)
    infrastructure_and_culture: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Actor Network and Information Requirements
# ---------------------------------------------------------------------------


class ActorNetworkScenarioOutput(StrictScenarioModel):
    """Organization-level actor network for planning handoff."""

    role: str = "actor_network"
    actors: list[dict[str, str]] = Field(default_factory=list)
    relationships: list[dict[str, str]] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


class InformationRequirement(StrictScenarioModel):
    """Human-reviewable information requirement, not a collection tasking."""

    category: str = "CIR"
    requirement: str = ""
    decision_supported: str = ""
    indicator: str = ""
    collection_question: str = ""
    recommended_owner: str = ""
    priority: str = ""


class InformationRequirementsScenarioOutput(StrictScenarioModel):
    role: str = "information_requirements"
    requirements: list[InformationRequirement] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# IPB Assistant
# ---------------------------------------------------------------------------


class IpbScenarioOutput(StrictScenarioModel):
    """Planning-level IPB scaffold built from the specialist handoffs."""

    role: str = "ipb"
    operational_environment: list[str] = Field(default_factory=list)
    environmental_effects: list[str] = Field(default_factory=list)
    broad_threat_or_hazard_patterns: list[str] = Field(default_factory=list)
    indicators_and_event_templates: list[str] = Field(default_factory=list)
    collection_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Assessment and Learning
# ---------------------------------------------------------------------------


class CorrectiveActionRecord(StrictScenarioModel):
    """Open corrective action captured from an AAR or assessment input."""

    observation: str = ""
    standard_or_measure: str = "Not provided"
    root_cause: str = "Not provided"
    corrective_action: str = "Not provided"
    owner: str = "Not provided — human assignment required"
    suspense: str = "Not provided — human assignment required"
    next_drill_verification_condition: str = "Not provided"


class AssessmentLearningScenarioOutput(StrictScenarioModel):
    role: str = "assessment_learning"
    corrective_action_register: list[CorrectiveActionRecord] = Field(default_factory=list)
    missing_evidence_or_ownership: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Union type and chain request
# ---------------------------------------------------------------------------

ScenarioOutput = (
    G9ScenarioOutput
    | S2ScenarioOutput
    | S4ScenarioOutput
    | S6ScenarioOutput
    | SurgeonScenarioOutput
    | SjaScenarioOutput
    | PaoScenarioOutput
    | XoScenarioOutput
    | OpsoScenarioOutput
    | ProvostScenarioOutput
    | G8ScenarioOutput
    | PlanningScenarioOutput
    | CoSScenarioOutput
    | FitnessScenarioOutput
    | OpsPtScenarioOutput
    | SelPtScenarioOutput
    | OrmPtScenarioOutput
    | AreaStudyScenarioOutput
    | ActorNetworkScenarioOutput
    | InformationRequirementsScenarioOutput
    | IpbScenarioOutput
    | AssessmentLearningScenarioOutput
)

SCENARIO_OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "g9": G9ScenarioOutput,
    "s2": S2ScenarioOutput,
    "s4": S4ScenarioOutput,
    "s6": S6ScenarioOutput,
    "planning": PlanningScenarioOutput,
    "cos": CoSScenarioOutput,
    "fitness": FitnessScenarioOutput,
    "surgeon": SurgeonScenarioOutput,
    "sja": SjaScenarioOutput,
    "pao": PaoScenarioOutput,
    "xo": XoScenarioOutput,
    "opso": OpsoScenarioOutput,
    "provost": ProvostScenarioOutput,
    "g8": G8ScenarioOutput,
    "opso_pt": OpsPtScenarioOutput,
    "cos_synthesis": RoundtableSynthesisOutput,
    "sel": SelPtScenarioOutput,
    "orm": OrmPtScenarioOutput,
    "area_study": AreaStudyScenarioOutput,
    "actor_network": ActorNetworkScenarioOutput,
    "information_requirements": InformationRequirementsScenarioOutput,
    "ipb": IpbScenarioOutput,
    "assessment_learning": AssessmentLearningScenarioOutput,
}


class ChainStep(BaseModel):
    agent_id: str
    input: str | None = None


class ChainRequest(BaseModel):
    scenario: str = Field(min_length=1)
    steps: list[ChainStep] = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    source_selection: SourceSelection | None = None
    external_processing_approval: ExternalProcessingApproval | None = None


class ChainStepResult(BaseModel):
    agent_id: str
    response: Any
    scenario_output: dict[str, Any] | None = None


class ChainResponse(BaseModel):
    scenario: str
    results: list[ChainStepResult]
    warnings: list[str] = Field(default_factory=list)
    completed: bool = True
    stopped_at_agent_id: str | None = None
    stopped_reason: str | None = None
