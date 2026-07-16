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
    role: str = "opso"
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
# Union type and chain request
# ---------------------------------------------------------------------------

ScenarioOutput = (
    G9ScenarioOutput
    | S2ScenarioOutput
    | S4ScenarioOutput
    | S6ScenarioOutput
    | PlanningScenarioOutput
    | CoSScenarioOutput
    | FitnessScenarioOutput
    | OpsPtScenarioOutput
    | SelPtScenarioOutput
    | OrmPtScenarioOutput
    | AreaStudyScenarioOutput
)

SCENARIO_OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "g9": G9ScenarioOutput,
    "s2": S2ScenarioOutput,
    "s4": S4ScenarioOutput,
    "s6": S6ScenarioOutput,
    "planning": PlanningScenarioOutput,
    "cos": CoSScenarioOutput,
    "fitness": FitnessScenarioOutput,
    "opso": OpsPtScenarioOutput,
    "sel": SelPtScenarioOutput,
    "orm": OrmPtScenarioOutput,
    "area_study": AreaStudyScenarioOutput,
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
