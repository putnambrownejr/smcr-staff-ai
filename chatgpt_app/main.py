from __future__ import annotations

import os
from typing import Any

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field, ValidationError

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def _tool_invocation_meta(in_progress: str, complete: str, *, read_only: bool) -> dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": in_progress,
        "openai/toolInvocation/invoked": complete,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": read_only,
        },
    }


adapter = ChatGptBridgeAdapter(
    base_url=os.getenv("SMCR_STAFF_AI_BACKEND_URL", "http://127.0.0.1:8000"),
    local_api_key=os.getenv("SMCR_STAFF_AI_LOCAL_API_KEY"),
)

mcp = FastMCP(
    name="smcr-staff-ai",
    stateless_http=True,
    transport_security=_transport_security_settings(),
)


class StaffPackageToolInput(BaseModel):
    title: str = Field(..., description="Short package title.")
    event_type: str = Field(default="drill_weekend", description="Training or event type.")
    mission_or_training_goal: str = Field(..., description="What the event is meant to achieve.")
    audience: str | None = Field(default=None, description="Who the package is for.")
    timeframe: str | None = Field(default=None, description="When the event will occur.")
    constraints: list[str] = Field(default_factory=list, description="Main planning constraints.")
    coordinating_sections: list[str] = Field(default_factory=list, description="Staff sections or support lanes.")
    support_requirements: list[str] = Field(default_factory=list, description="Broad support needs.")
    partner_types: list[str] = Field(default_factory=list, description="External partners or role players.")
    civil_considerations: list[str] = Field(default_factory=list, description="Civil or population factors.")
    medical_risk_context: list[str] = Field(default_factory=list, description="Medical risk factors.")
    casualty_scenarios: list[str] = Field(default_factory=list, description="Training-safe casualty scenarios.")
    source_items: list[dict[str, str]] = Field(default_factory=list, description="Optional open-source context items.")
    intelligence_question: str | None = Field(default=None, description="Optional S-2 question.")
    c2_objective: str | None = Field(default=None, description="Optional comm/C2 objective.")
    support_objective: str | None = Field(default=None, description="Optional S-4 objective.")
    include_g9: bool | None = Field(default=None, description="Whether to force G-9 review.")
    product_types: list[str] = Field(default_factory=lambda: ["warno", "frago", "aar"])
    preferred_format: str | None = Field(default=None, description="Optional preferred output format.")
    training_only: bool = Field(default=True, description="Set true for training-only or fictional scenarios.")


class StaffProductToolInput(BaseModel):
    product_type: str = Field(..., description="Product type such as warno, frago, aar, or naval_letter.")
    topic: str = Field(..., description="Topic or purpose of the product.")
    audience: str | None = Field(default=None, description="Who the product is for.")
    echelon: str | None = Field(default=None, description="Command echelon.")
    preferred_format: str | None = Field(default=None, description="Formatting preference if applicable.")
    facts: list[str] = Field(default_factory=list, description="Known facts to incorporate.")
    constraints: list[str] = Field(default_factory=list, description="Known constraints to respect.")
    training_or_fictional: bool = Field(default=True, description="Whether the scenario is training-only.")
    include_review_checklist: bool = Field(default=True, description="Whether to include the review checklist.")


class FragoToConopToolInput(BaseModel):
    title: str = Field(..., description="Short package title.")
    supported_echelon: str = Field(
        default="company",
        description="Supported echelon such as company or battalion.",
    )
    higher_headquarters: str | None = Field(
        default=None,
        description="Higher headquarters issuing or shaping guidance.",
    )
    supported_unit: str = Field(..., description="Unit building the initial CONOP.")
    event_type: str = Field(default="training_event", description="Event or planning type.")
    mission_or_training_goal: str = Field(..., description="What the event or guidance is meant to achieve.")
    raw_guidance_text: str | None = Field(default=None, description="Optional pasted higher guidance or FRAGO text.")
    higher_guidance: list[str] = Field(default_factory=list, description="Key higher-guidance statements.")
    frago_facts: list[str] = Field(default_factory=list, description="Known FRAGO facts or directions to preserve.")
    s3_inputs: list[str] = Field(default_factory=list, description="S-3 planning inputs.")
    g9_inputs: list[str] = Field(default_factory=list, description="G-9 or civil-consideration inputs.")
    source_items: list[dict[str, str]] = Field(default_factory=list, description="Optional public-source context.")
    intelligence_question: str | None = Field(default=None, description="Optional S-2 question.")
    subordinate_units: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Subordinate or supporting units.",
    )
    met_tasks: list[str] = Field(default_factory=list, description="Relevant MET-aligned tasks.")
    metl_focus: list[str] = Field(default_factory=list, description="Relevant METL focus.")
    constraints: list[str] = Field(default_factory=list, description="Key constraints.")
    support_requirements: list[str] = Field(default_factory=list, description="Support requirements to preserve.")
    coordinating_sections: list[str] = Field(default_factory=list, description="Coordinating staff sections.")
    partner_types: list[str] = Field(default_factory=list, description="External partners or role players.")
    civil_considerations: list[str] = Field(default_factory=list, description="Civil or population considerations.")
    medical_risk_context: list[str] = Field(default_factory=list, description="Medical-risk context.")
    casualty_scenarios: list[str] = Field(default_factory=list, description="Training-safe casualty scenarios.")
    timeframe: str | None = Field(default=None, description="Optional timeframe.")
    preferred_format: str | None = Field(default=None, description="Preferred format if known.")
    formal_event: bool = Field(default=False, description="Whether to trigger XO/SEL formal-event review.")
    include_tdg: bool = Field(
        default=True,
        description="Whether to include the linked S-3 TDG / wargaming package in the response.",
    )
    training_only: bool = Field(default=True, description="Set true for training-only or fictional scenarios.")


class CaseStudyToolInput(BaseModel):
    title: str = Field(..., description="Short case-study title.")
    framing_question: str = Field(..., description="What the audience should decide or learn from the case.")
    training_objective: str = Field(..., description="The training objective the case is meant to sharpen.")
    audience: str | None = Field(default=None, description="Intended audience for the discussion or PME.")
    source_items: list[dict[str, str]] = Field(
        default_factory=list,
        description="Optional public-source items to ground the case in current events or real examples.",
    )
    current_event_context: list[str] = Field(
        default_factory=list,
        description="Optional short current-event facts or themes to shape the case.",
    )
    met_tasks: list[str] = Field(default_factory=list, description="Relevant MET-aligned tasks.")
    metl_focus: list[str] = Field(default_factory=list, description="Relevant METL focus areas.")
    constraints: list[str] = Field(default_factory=list, description="Discussion or planning constraints to preserve.")
    training_only: bool = Field(default=True, description="Set true for training-only or fictional framing.")


class TdgToolInput(BaseModel):
    title: str = Field(..., description="Short TDG or wargaming title.")
    theme: str = Field(..., description="Core tactical or decision-making theme.")
    audience: str | None = Field(default=None, description="Intended audience for the TDG.")
    training_objective: str = Field(..., description="What judgment or habit the TDG should sharpen.")
    scenario_context: list[str] = Field(default_factory=list, description="Optional scenario frame inputs.")
    opposing_factors: list[str] = Field(default_factory=list, description="Optional opposing factors or friction.")
    friendly_forces: list[str] = Field(default_factory=list, description="Optional friendly-force realities.")
    civil_considerations: list[str] = Field(default_factory=list, description="Optional civil considerations.")
    reserve_friction: list[str] = Field(default_factory=list, description="Optional reserve-specific friction.")
    decision_time: str | None = Field(default=None, description="Optional time available for the decision.")
    references: list[str] = Field(default_factory=list, description="Optional doctrinal or PME references.")
    constraints: list[str] = Field(default_factory=list, description="Session or scenario constraints.")
    include_red_team: bool = Field(default=True, description="Whether to include red-team critique prompts.")
    include_sketch_map_prompt: bool = Field(
        default=True,
        description="Whether to include a sketch-map prompt for instructor use.",
    )


class InfantryTrainingPackageToolInput(BaseModel):
    title: str = Field(..., description="Short package title.")
    training_goal: str = Field(..., description="What the package is meant to train.")
    unit_name: str | None = Field(default=None, description="Optional unit name.")
    audience: str | None = Field(default=None, description="Optional audience description.")
    primary_training_population: str = Field(
        default="non-03 support Marines",
        description="Who the package is mainly built for.",
    )
    venue_type: str = Field(default="MOUT town", description="Training venue or urban site type.")
    ammunition_type: str = Field(default="blank ammunition", description="Training ammunition type.")
    training_window: str | None = Field(default=None, description="Available training window.")
    constraints: list[str] = Field(default_factory=list, description="Key constraints.")
    support_requirements: list[str] = Field(default_factory=list, description="Support dependencies to verify.")
    met_tasks: list[str] = Field(default_factory=list, description="Relevant MET-aligned tasks.")
    metl_focus: list[str] = Field(default_factory=list, description="Relevant METL focus.")
    training_only: bool = Field(default=True, description="Set true for training-only framing.")


class StaffSectionUpdateToolInput(BaseModel):
    section: str = Field(..., description="Staff section label such as S-3 or S-4.")
    summary: str = Field(..., description="Current section summary in plain staff language.")
    changes_since_last: list[str] = Field(default_factory=list, description="What changed since the last update.")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions still driving the section view.")
    open_issues: list[str] = Field(default_factory=list, description="Open issues the section is carrying.")
    support_requests: list[str] = Field(default_factory=list, description="Support requests or dependencies.")
    decisions_needed: list[str] = Field(default_factory=list, description="Commander or XO decisions needed.")
    risks: list[str] = Field(default_factory=list, description="Main risks or friction points.")
    next_24_72: list[str] = Field(default_factory=list, description="What the section owes in the next 24 to 72 hours.")
    adjacent_section_asks: list[str] = Field(
        default_factory=list,
        description="What this section needs from adjacent staff.",
    )


class StaffUpdateCycleToolInput(BaseModel):
    title: str = Field(..., description="Short update-cycle title.")
    supported_unit: str = Field(..., description="Unit receiving the update cycle.")
    supported_echelon: str = Field(default="company", description="Supported echelon such as company or battalion.")
    event_type: str = Field(default="training_event", description="Planning or event type.")
    mission_or_training_goal: str = Field(..., description="What the unit is trying to accomplish.")
    timeframe: str | None = Field(default=None, description="Optional update horizon.")
    time_available: str | None = Field(default=None, description="Optional time available for planning.")
    commander_priorities: list[str] = Field(default_factory=list, description="Commander priorities for this cycle.")
    higher_guidance: list[str] = Field(default_factory=list, description="Higher guidance to preserve.")
    constraints: list[str] = Field(default_factory=list, description="Key planning constraints.")
    coordinating_sections: list[str] = Field(default_factory=list, description="Staff sections that owe estimates.")
    support_requirements: list[str] = Field(default_factory=list, description="Support dependencies to verify.")
    partner_types: list[str] = Field(default_factory=list, description="Relevant external partners.")
    civil_considerations: list[str] = Field(default_factory=list, description="Relevant civil considerations.")
    met_tasks: list[str] = Field(default_factory=list, description="Relevant MET-aligned tasks.")
    metl_focus: list[str] = Field(default_factory=list, description="Relevant METL focus.")
    focus_sections: list[str] = Field(
        default_factory=list,
        description="Optional section lanes to emphasize for gap-cover or thin-bench support.",
    )
    section_updates: list[StaffSectionUpdateToolInput] = Field(
        default_factory=list,
        description="Structured section updates feeding the running estimate, CUB, and CPB.",
    )
    training_only: bool = Field(default=True, description="Set true for training-only or fictional scenarios.")


class AgentRunToolInput(BaseModel):
    agent_id: str = Field(..., description="Registered staff or specialty agent id.")
    input: str = Field(..., description="The actual user question or task for the agent.")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional agent context.")


class StaffAgentAssistToolInput(BaseModel):
    input: str = Field(..., description="The actual user question or staff problem for this lane.")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional agent context.")


class ChiefBriefToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    include_personal_documents: bool = Field(default=True, description="Include local document summary.")
    include_drill_plans: bool = Field(default=True, description="Include stored drill plans.")
    maradmin_records: list[dict[str, Any]] = Field(default_factory=list, description="Optional MARADMIN inputs.")


class UserKeyToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")


class ActiveUserContextToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    unit_name: str | None = Field(default=None, description="Temporary unit name.")
    unit_type: str | None = Field(default=None, description="Temporary unit type or formation.")
    unit_family: str | None = Field(default=None, description="Temporary community or unit family.")
    billet_override: str | None = Field(default=None, description="Temporary billet emphasis.")
    mos_override: str | None = Field(default=None, description="Temporary MOS emphasis.")
    current_focus: list[str] = Field(default_factory=list, description="Short-term focus areas.")
    staff_bias: list[str] = Field(default_factory=list, description="Bias cues for staff-agent advice.")
    temporary_notes: list[str] = Field(default_factory=list, description="Short-lived shaping notes.")
    preferences: dict[str, str] = Field(default_factory=dict, description="Small temporary preferences map.")
    expires_at: str | None = Field(default=None, description="Optional ISO timestamp for expiration.")


class SectionMemoryEntryToolInput(BaseModel):
    section: str = Field(..., description="Section lane such as S-4, S-6, XO/Chief, or SEL.")
    title: str = Field(..., description="Short label for the recurring memory item.")
    recurring_questions: list[str] = Field(default_factory=list, description="Questions this lane usually needs asked.")
    recurring_failure_modes: list[str] = Field(
        default_factory=list,
        description="Ways this lane usually fails or drifts.",
    )
    preferred_checks: list[str] = Field(
        default_factory=list,
        description="Checks or prompts that keep this lane honest.",
    )
    notes: list[str] = Field(default_factory=list, description="Short reusable notes for this lane.")


class SectionMemoryToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    entries: list[SectionMemoryEntryToolInput] = Field(
        default_factory=list,
        description="Local section-memory entries.",
    )


class AdminWorkflowToolInput(BaseModel):
    workflow_type: str = Field(..., description="Workflow type such as gtcc, dts_authorization, or award_package.")
    title: str = Field(..., description="Short workflow title.")
    facts: list[str] = Field(default_factory=list, description="Facts relevant to the workflow.")
    constraints: list[str] = Field(default_factory=list, description="Constraints that shape the workflow.")


class ReminderPlanToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    include_travel_tasks: bool = Field(default=True, description="Include travel-related reminder tasks.")
    only_future_drills: bool = Field(default=True, description="Only generate plans for current or future drill dates.")


class ExternalAiPacketToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    target_platform: str = Field(
        default="generic",
        description="Hosted AI target: generic, claude, gemini, grok, copilot, or genai.",
    )
    include_handoff: bool = Field(default=True, description="Include the scrubbed long-term handoff.")
    include_active_user_context: bool = Field(
        default=True,
        description="Include the scrubbed temporary active user context.",
    )
    include_document_summary: bool = Field(
        default=False,
        description="Include only aggregate local document counts and warnings.",
    )
    include_drill_plans: bool = Field(
        default=False,
        description="Include scrubbed drill-plan task summaries.",
    )
    include_opportunities: bool = Field(
        default=False,
        description="Include scrubbed opportunity summaries.",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include recommended share framing and warnings.",
    )
    purpose: str | None = Field(
        default=None,
        description="What the outside model is being asked to help with.",
    )


TOOL_SPECS: list[types.Tool] = [
    types.Tool(
        name="build_staff_package",
        title="Build Staff Package",
        description=(
            "Use this when the user wants one reserve training or event problem turned into a full staff package "
            "with S-2, S-3, S-4, S-6, medical, staff review, XO vet, and recommended products."
        ),
        inputSchema=StaffPackageToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the staff package", "Staff package ready", read_only=False),
    ),
    types.Tool(
        name="draft_staff_product",
        title="Draft Staff Product",
        description=(
            "Use this when the user needs an advisory WARNO, FRAGO, AAR, decision brief, command-update brief, "
            "naval letter, memorandum, or similar staff product scaffold."
        ),
        inputSchema=StaffProductToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Drafting the staff product", "Staff product draft ready", read_only=False),
    ),
    types.Tool(
        name="build_frago_to_conop",
        title="Build FRAGO To CONOP",
        description=(
            "Use this when the user has higher guidance or a training FRAGO and wants an initial CONOP, "
            "unit/sub-unit task framing, MET/METL alignment, and XO/SEL-ready AAR structure."
        ),
        inputSchema=FragoToConopToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the FRAGO-to-CONOP package",
            "FRAGO-to-CONOP package ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_training_case_study",
        title="Build Training Case Study",
        description=(
            "Use this when the user wants an S-3-led training case study grounded in public-source context, "
            "with optional S-2 framing, MET/METL alignment, CONOP implications, and AAR discussion focus."
        ),
        inputSchema=CaseStudyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the case study", "Training case study ready", read_only=False),
    ),
    types.Tool(
        name="build_tdg",
        title="Build TDG Or Wargame",
        description=(
            "Use this when the user wants an S-3-style tactical decision game or short wargaming scaffold to "
            "stress assumptions, decision points, and reserve-specific friction."
        ),
        inputSchema=TdgToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the TDG", "TDG ready", read_only=False),
    ),
    types.Tool(
        name="build_infantry_training_package",
        title="Build Infantry Training Package",
        description=(
            "Use this when the user wants a training-safe 03xx-style familiarization package, especially for "
            "non-03 Marines, blanks, MOUT sites, and modified urban lanes that need scope discipline."
        ),
        inputSchema=InfantryTrainingPackageToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the infantry training package",
            "Infantry training package ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_mission_analysis",
        title="Build Mission Analysis",
        description=(
            "Use this when the user wants a mission-analysis worksheet with specified and implied tasks, "
            "constraints, assumptions, information requirements, and staff-estimate due-outs."
        ),
        inputSchema=StaffUpdateCycleToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building mission analysis",
            "Mission analysis ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_planning_cell",
        title="Build Planning Cell",
        description=(
            "Use this when the user wants a planning-cell package that ties mission analysis, planning approach, "
            "assumption and decision logs, and the running estimate/CUB/CPB cycle together."
        ),
        inputSchema=StaffUpdateCycleToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the planning cell package",
            "Planning cell package ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_lone_planner",
        title="Build Lone Planner Assist",
        description=(
            "Use this when the user is thin-staffed or working alone and needs a walk-in brief, likely blind spots, "
            "cross-lane asks, immediate actions, and a linked planning-cell package."
        ),
        inputSchema=StaffUpdateCycleToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the lone planner assist package",
            "Lone planner assist ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_assisted_section_estimates",
        title="Build Assisted Section Estimates",
        description=(
            "Use this when the user has partial staff coverage and needs disciplined gap-cover scaffolds for missing "
            "lanes such as S-1/Admin, S-4, S-6, medical, XO/Chief, or SEL before briefing the XO or commander."
        ),
        inputSchema=StaffUpdateCycleToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the assisted section estimates",
            "Assisted section estimates ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_staff_update_cycle",
        title="Build Staff Update Cycle",
        description=(
            "Use this when the user has section updates and wants a linked running estimate, CUB, and CPB "
            "instead of a one-off product draft."
        ),
        inputSchema=StaffUpdateCycleToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the staff update cycle",
            "Staff update cycle ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_sja_military_justice_advisor",
        title="Run SJA Military Justice Advisor",
        description=(
            "Use this when the user wants SJA-style command issue-spotting for NJP, UCMJ, courts-martial, "
            "Reserve-status jurisdiction questions, or military justice routing."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the SJA advisor",
            "SJA military justice advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_infantry_03xx_advisor",
        title="Run Infantry 03XX Advisor",
        description=(
            "Use this when the user wants S-3-family infantry training help, including familiarization, "
            "basic tactical framing, patrolling refreshers, urban training scope control, and leader rehearsal."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the infantry advisor",
            "Infantry 03XX advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_patrolling_refresher",
        title="Run Patrolling Refresher",
        description=(
            "Use this when the user wants a compact patrolling refresher focused on simple fundamentals, "
            "control measures, reporting, leader checks, and training-safe repetition."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the patrolling refresher",
            "Patrolling refresher ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_blank_fire_urban_lane",
        title="Run Blank-Fire Urban Lane",
        description=(
            "Use this when the user wants a training-safe blank-fire urban lane focused on scope control, "
            "leader supervision, sectors, reporting, casualty actions, and blank-fire discipline."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the blank-fire urban lane",
            "Blank-fire urban lane ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_leader_rehearsal_oic_worksheet",
        title="Run Leader Rehearsal OIC Worksheet",
        description=(
            "Use this when the user wants an OIC-style worksheet for leader rehearsals, control measures, "
            "stop-training criteria, safety, medical checks, and AAR setup."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the OIC worksheet",
            "Leader rehearsal OIC worksheet ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_njp_issue_spotting_worksheet",
        title="Run NJP Issue Spotting Worksheet",
        description=(
            "Use this when the user wants a compact NJP worksheet covering authority, jurisdiction, accused "
            "advice, punishments, Reserve concerns, UPB discipline, and what must go to the SJA."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the NJP worksheet",
            "NJP issue-spotting worksheet ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_military_justice_routing_checklist",
        title="Run Military Justice Routing Checklist",
        description=(
            "Use this when the user wants a compact routing checklist for whether a matter belongs with SJA, "
            "defense, VLC, trial services, or another military justice channel."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the routing checklist",
            "Military justice routing checklist ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_opt_facilitator",
        title="Run OPT Facilitator",
        description=(
            "Use this when the user wants help running mission analysis or an OPT with visible assumptions, "
            "decisions, questions, and due-outs."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Running the OPT facilitator", "OPT facilitator ready", read_only=False),
    ),
    types.Tool(
        name="run_red_team_assumptions_challenge",
        title="Run Red Team Challenge",
        description=(
            "Use this when the user wants a plan, brief, or COA pressure-tested for weak assumptions, "
            "fake alternatives, and polite groupthink."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Running the red-team challenge", "Red-team challenge ready", read_only=False),
    ),
    types.Tool(
        name="run_assessment_learning_advisor",
        title="Run Assessment Learning Advisor",
        description=(
            "Use this when the user wants to connect MET/METL, AAR observations, corrective actions, "
            "and next-drill follow-through."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the assessment advisor",
            "Assessment learning advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_writing_briefing_coach",
        title="Run Writing Briefing Coach",
        description=(
            "Use this when the user wants a brief or staff product tightened around audience, decision, "
            "structure, evidence, and brevity."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the writing coach",
            "Writing briefing coach ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_joint_interagency_frame_advisor",
        title="Run Joint Interagency Frame Advisor",
        description=(
            "Use this when the user wants help widening the frame around command relationships, outside actors, "
            "and coordination assumptions."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the joint interagency advisor",
            "Joint interagency advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_mos_adjutant_0102_advisor",
        title="Run MOS 0102 Adjutant Advisor",
        description=(
            "Use this when the user wants the 0102 officer slice under S-1: accountability, correspondence, "
            "awards, staffing discipline, and reserve admin continuity."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the 0102 adjutant advisor",
            "MOS 0102 adjutant advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_mos_logistics_0402_advisor",
        title="Run MOS 0402 Logistics Officer Advisor",
        description=(
            "Use this when the user wants the 0402 officer slice under S-4: supportability, sustainment judgment, "
            "lead times, movement friction, and what breaks the plan first."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the 0402 logistics advisor",
            "MOS 0402 logistics advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_mos_supply_3002_advisor",
        title="Run MOS 3002 Supply Officer Advisor",
        description=(
            "Use this when the user wants the 3002 officer slice under S-4: supply accountability, fiscal "
            "discipline, inventory readiness, and command supply risk."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the 3002 supply advisor",
            "MOS 3002 supply advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="run_mos_magtf_planner_0511_advisor",
        title="Run MOS 0511 MAGTF Planner Advisor",
        description=(
            "Use this when the user wants the 0511 planner slice under S-3: mission analysis, planning support, "
            "assumption control, and staff-integration discipline."
        ),
        inputSchema=StaffAgentAssistToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Running the 0511 MAGTF planner advisor",
            "MOS 0511 MAGTF planner advisor ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="list_staff_agents",
        title="List Staff Agents",
        description="Use this when the user wants to see which staff and specialty agents are available.",
        inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        _meta=_tool_invocation_meta("Loading staff agents", "Staff agents listed", read_only=True),
    ),
    types.Tool(
        name="run_staff_agent",
        title="Run Staff Agent",
        description="Use this when the user wants targeted help from one specific staff or specialty agent.",
        inputSchema=AgentRunToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Running the staff agent", "Staff agent response ready", read_only=False),
    ),
    types.Tool(
        name="build_chief_brief",
        title="Build Chief Brief",
        description=(
            "Use this when the user wants a personal Chief of Staff/Aide triage brief "
            "based on their saved local context."
        ),
        inputSchema=ChiefBriefToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the Chief brief", "Chief brief ready", read_only=False),
    ),
    types.Tool(
        name="build_next_drill_readiness",
        title="Build Next Drill Readiness",
        description=(
            "Use this when the user wants the most practical front door for what matters before next drill: "
            "immediate actions, friction points, missing foundation, standing rhythm, and follow-on workflows."
        ),
        inputSchema=ChiefBriefToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building next-drill readiness",
            "Next-drill readiness ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="build_walk_in_brief_pack",
        title="Build Walk-In Brief Pack",
        description=(
            "Use this when the user wants the fastest continuity picture before a sync, call, or drill walk-in: "
            "what changed, what is stale, what still needs a decision, and what to carry in cold."
        ),
        inputSchema=ChiefBriefToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Building the walk-in brief pack",
            "Walk-in brief pack ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="career_watch",
        title="Career Watch",
        description=(
            "Use this when the user wants PME, FitRep, document, and opportunity awareness "
            "for a saved profile."
        ),
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Reviewing career watch", "Career watch ready", read_only=True),
    ),
    types.Tool(
        name="admin_readiness",
        title="Admin Readiness",
        description="Use this when the user wants S-1/Admin readiness status for a saved local profile.",
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Reviewing admin readiness", "Admin readiness ready", read_only=True),
    ),
    types.Tool(
        name="build_admin_workflow",
        title="Build Admin Workflow",
        description=(
            "Use this when the user needs an S-1 style GTCC, DTS, orders, awards, or admin-package workflow checklist."
        ),
        inputSchema=AdminWorkflowToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the admin workflow", "Admin workflow ready", read_only=False),
    ),
    types.Tool(
        name="build_handoff_reminder_plans",
        title="Build Handoff Reminder Plans",
        description=(
            "Use this when the user wants stored drill rhythm, recurring checks, and recurring drill notes turned "
            "into actual reminder-plan outputs."
        ),
        inputSchema=ReminderPlanToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building reminder plans", "Reminder plans ready", read_only=False),
    ),
    types.Tool(
        name="build_external_ai_packet",
        title="Build External AI Packet",
        description=(
            "Use this when the user wants a share-safe packet for Claude, Gemini, Grok, Copilot, GENAI, "
            "or another hosted model without exposing raw local records by default."
        ),
        inputSchema=ExternalAiPacketToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Preparing the external AI packet",
            "External AI packet ready",
            read_only=False,
        ),
    ),
    types.Tool(
        name="get_active_user_context",
        title="Get Active User Context",
        description=(
            "Use this when the user wants to see the current temporary local context that biases staff or agent output."
        ),
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Loading active context", "Active context ready", read_only=True),
    ),
    types.Tool(
        name="set_active_user_context",
        title="Set Active User Context",
        description=(
            "Use this when the user wants to temporarily shape advice by setting a current unit, billet, "
            "community, or short-term focus without overwriting the longer-term handoff."
        ),
        inputSchema=ActiveUserContextToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Saving active context", "Active context saved", read_only=False),
    ),
    types.Tool(
        name="get_section_memory_profile",
        title="Get Section Memory Profile",
        description=(
            "Use this when the user wants to read local recurring staff-memory notes for sections like S-4, "
            "S-6, XO/Chief, or SEL."
        ),
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Loading section memory",
            "Section memory ready",
            read_only=True,
        ),
    ),
    types.Tool(
        name="set_section_memory_profile",
        title="Set Section Memory Profile",
        description=(
            "Use this when the user wants to save local recurring staff-memory notes, usual failure modes, "
            "questions, and checks for specific sections."
        ),
        inputSchema=SectionMemoryToolInput.model_json_schema(),
        _meta=_tool_invocation_meta(
            "Saving section memory",
            "Section memory saved",
            read_only=False,
        ),
    ),
]


@mcp._mcp_server.list_tools()  # type: ignore[untyped-decorator,no-untyped-call]
async def _list_tools() -> list[types.Tool]:
    return TOOL_SPECS


def _ok_result(message: str, payload: dict[str, Any]) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            structuredContent=payload,
            isError=False,
        )
    )


def _error_result(message: str) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            isError=True,
        )
    )


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    name = req.params.name
    arguments = req.params.arguments or {}

    try:
        if name == "build_staff_package":
            staff_package_payload = StaffPackageToolInput.model_validate(arguments)
            result = await adapter.build_staff_package(staff_package_payload.model_dump())
            return _ok_result("Built the staff package.", result)

        if name == "draft_staff_product":
            staff_product_payload = StaffProductToolInput.model_validate(arguments)
            result = await adapter.draft_staff_product(staff_product_payload.model_dump())
            return _ok_result("Drafted the staff product.", result)

        if name == "build_frago_to_conop":
            frago_payload = FragoToConopToolInput.model_validate(arguments)
            result = await adapter.build_frago_to_conop(frago_payload.model_dump())
            return _ok_result("Built the FRAGO-to-CONOP package.", result)

        if name == "build_training_case_study":
            case_study_payload = CaseStudyToolInput.model_validate(arguments)
            result = await adapter.build_training_case_study(case_study_payload.model_dump())
            return _ok_result("Built the training case study.", result)

        if name == "build_tdg":
            tdg_payload = TdgToolInput.model_validate(arguments)
            result = await adapter.build_tdg(tdg_payload.model_dump())
            return _ok_result("Built the TDG or wargame.", result)

        if name == "build_infantry_training_package":
            infantry_package_payload = InfantryTrainingPackageToolInput.model_validate(arguments)
            result = await adapter.build_infantry_training_package(infantry_package_payload.model_dump())
            return _ok_result("Built the infantry training package.", result)

        if name == "build_mission_analysis":
            mission_analysis_payload = StaffUpdateCycleToolInput.model_validate(arguments)
            result = await adapter.build_mission_analysis(mission_analysis_payload.model_dump())
            return _ok_result("Built mission analysis.", result)

        if name == "build_planning_cell":
            planning_cell_payload = StaffUpdateCycleToolInput.model_validate(arguments)
            result = await adapter.build_planning_cell(planning_cell_payload.model_dump())
            return _ok_result("Built the planning cell package.", result)

        if name == "build_lone_planner":
            lone_planner_payload = StaffUpdateCycleToolInput.model_validate(arguments)
            result = await adapter.build_lone_planner(lone_planner_payload.model_dump())
            return _ok_result("Built the lone planner assist package.", result)

        if name == "build_assisted_section_estimates":
            section_estimate_payload = StaffUpdateCycleToolInput.model_validate(arguments)
            result = await adapter.build_assisted_section_estimates(section_estimate_payload.model_dump())
            return _ok_result("Built the assisted section estimates.", result)

        if name == "build_staff_update_cycle":
            update_cycle_payload = StaffUpdateCycleToolInput.model_validate(arguments)
            result = await adapter.build_staff_update_cycle(update_cycle_payload.model_dump())
            return _ok_result("Built the staff update cycle.", result)

        if name == "run_opt_facilitator":
            opt_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_opt_facilitator(
                {"input": opt_payload.input, "context": opt_payload.context}
            )
            return _ok_result("Ran the OPT facilitator.", result)

        if name == "run_sja_military_justice_advisor":
            sja_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_sja_military_justice_advisor(
                {"input": sja_payload.input, "context": sja_payload.context}
            )
            return _ok_result("Ran the SJA military justice advisor.", result)

        if name == "run_infantry_03xx_advisor":
            infantry_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_infantry_03xx_advisor(
                {"input": infantry_payload.input, "context": infantry_payload.context}
            )
            return _ok_result("Ran the infantry 03XX advisor.", result)

        if name == "run_patrolling_refresher":
            patrolling_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_patrolling_refresher(
                {"input": patrolling_payload.input, "context": patrolling_payload.context}
            )
            return _ok_result("Ran the patrolling refresher.", result)

        if name == "run_blank_fire_urban_lane":
            urban_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_blank_fire_urban_lane(
                {"input": urban_payload.input, "context": urban_payload.context}
            )
            return _ok_result("Ran the blank-fire urban lane.", result)

        if name == "run_leader_rehearsal_oic_worksheet":
            worksheet_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_leader_rehearsal_oic_worksheet(
                {"input": worksheet_payload.input, "context": worksheet_payload.context}
            )
            return _ok_result("Ran the leader rehearsal OIC worksheet.", result)

        if name == "run_njp_issue_spotting_worksheet":
            njp_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_njp_issue_spotting_worksheet(
                {"input": njp_payload.input, "context": njp_payload.context}
            )
            return _ok_result("Ran the NJP issue-spotting worksheet.", result)

        if name == "run_military_justice_routing_checklist":
            routing_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_military_justice_routing_checklist(
                {"input": routing_payload.input, "context": routing_payload.context}
            )
            return _ok_result("Ran the military justice routing checklist.", result)

        if name == "run_red_team_assumptions_challenge":
            red_team_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_red_team_assumptions_challenge(
                {"input": red_team_payload.input, "context": red_team_payload.context}
            )
            return _ok_result("Ran the red-team assumptions challenge.", result)

        if name == "run_assessment_learning_advisor":
            assessment_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_assessment_learning_advisor(
                {"input": assessment_payload.input, "context": assessment_payload.context}
            )
            return _ok_result("Ran the assessment learning advisor.", result)

        if name == "run_writing_briefing_coach":
            writing_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_writing_briefing_coach(
                {"input": writing_payload.input, "context": writing_payload.context}
            )
            return _ok_result("Ran the writing briefing coach.", result)

        if name == "run_joint_interagency_frame_advisor":
            joint_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_joint_interagency_frame_advisor(
                {"input": joint_payload.input, "context": joint_payload.context}
            )
            return _ok_result("Ran the joint interagency frame advisor.", result)

        if name == "run_mos_adjutant_0102_advisor":
            mos_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_mos_adjutant_0102_advisor(
                {"input": mos_payload.input, "context": mos_payload.context}
            )
            return _ok_result("Ran the MOS 0102 adjutant advisor.", result)

        if name == "run_mos_logistics_0402_advisor":
            mos_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_mos_logistics_0402_advisor(
                {"input": mos_payload.input, "context": mos_payload.context}
            )
            return _ok_result("Ran the MOS 0402 logistics advisor.", result)

        if name == "run_mos_supply_3002_advisor":
            mos_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_mos_supply_3002_advisor(
                {"input": mos_payload.input, "context": mos_payload.context}
            )
            return _ok_result("Ran the MOS 3002 supply advisor.", result)

        if name == "run_mos_magtf_planner_0511_advisor":
            mos_payload = StaffAgentAssistToolInput.model_validate(arguments)
            result = await adapter.run_mos_magtf_planner_0511_advisor(
                {"input": mos_payload.input, "context": mos_payload.context}
            )
            return _ok_result("Ran the MOS 0511 MAGTF planner advisor.", result)

        if name == "list_staff_agents":
            result = await adapter.list_agents()
            return _ok_result("Listed the available staff agents.", result)

        if name == "run_staff_agent":
            agent_payload = AgentRunToolInput.model_validate(arguments)
            result = await adapter.run_staff_agent(
                agent_id=agent_payload.agent_id,
                payload={"input": agent_payload.input, "context": agent_payload.context},
            )
            return _ok_result(f"Ran the {agent_payload.agent_id} agent.", result)

        if name == "build_chief_brief":
            chief_payload = ChiefBriefToolInput.model_validate(arguments)
            result = await adapter.build_chief_brief(chief_payload.model_dump())
            return _ok_result("Built the Chief brief.", result)

        if name == "build_next_drill_readiness":
            readiness_payload = ChiefBriefToolInput.model_validate(arguments)
            result = await adapter.build_next_drill_readiness(readiness_payload.model_dump())
            return _ok_result("Built next-drill readiness.", result)

        if name == "build_walk_in_brief_pack":
            walk_in_payload = ChiefBriefToolInput.model_validate(arguments)
            result = await adapter.build_walk_in_brief_pack(walk_in_payload.model_dump())
            return _ok_result("Built the walk-in brief pack.", result)

        if name == "career_watch":
            user_key_payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_career_watch(user_key=user_key_payload.user_key)
            return _ok_result("Built the career watch.", result)

        if name == "admin_readiness":
            user_key_payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_admin_readiness(user_key=user_key_payload.user_key)
            return _ok_result("Built the admin readiness summary.", result)

        if name == "build_admin_workflow":
            workflow_payload = AdminWorkflowToolInput.model_validate(arguments)
            result = await adapter.build_admin_workflow(workflow_payload.model_dump())
            return _ok_result("Built the admin workflow.", result)

        if name == "build_handoff_reminder_plans":
            reminder_payload = ReminderPlanToolInput.model_validate(arguments)
            result = await adapter.build_handoff_reminder_plans(
                user_key=reminder_payload.user_key,
                payload={
                    "include_travel_tasks": reminder_payload.include_travel_tasks,
                    "only_future_drills": reminder_payload.only_future_drills,
                },
            )
            return _ok_result("Built the handoff reminder plans.", result)

        if name == "build_external_ai_packet":
            external_packet_payload = ExternalAiPacketToolInput.model_validate(arguments)
            result = await adapter.build_external_ai_packet(external_packet_payload.model_dump())
            return _ok_result("Built the external AI packet.", result)

        if name == "get_active_user_context":
            user_key_payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_active_user_context(user_key=user_key_payload.user_key)
            return _ok_result("Loaded the active user context.", result)

        if name == "set_active_user_context":
            active_context_payload = ActiveUserContextToolInput.model_validate(arguments)
            result = await adapter.set_active_user_context(
                user_key=active_context_payload.user_key,
                payload=active_context_payload.model_dump(),
            )
            return _ok_result("Saved the active user context.", result)

        if name == "get_section_memory_profile":
            user_key_payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_section_memory_profile(user_key=user_key_payload.user_key)
            return _ok_result("Loaded the section memory profile.", result)

        if name == "set_section_memory_profile":
            section_memory_payload = SectionMemoryToolInput.model_validate(arguments)
            result = await adapter.set_section_memory_profile(
                user_key=section_memory_payload.user_key,
                payload={"entries": [item.model_dump() for item in section_memory_payload.entries]},
            )
            return _ok_result("Saved the section memory profile.", result)

        return _error_result(f"Unknown tool: {name}")
    except ValidationError as exc:
        return _error_result(f"Input validation error: {exc.errors()}")
    except Exception as exc:  # pragma: no cover - transport-facing guardrail
        return _error_result(f"Tool execution failed: {exc}")


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request

app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("chatgpt_app.main:app", host="0.0.0.0", port=8001)
