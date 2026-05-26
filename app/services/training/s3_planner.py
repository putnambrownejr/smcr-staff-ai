from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import (
    S3PlanningRequest,
    S3PlanningResponse,
    S3SubordinatePromptPacket,
    S3SubordinateUnitInput,
)
from app.services.training.scenario_engine import build_s3_scenario_design


class S3Planner:
    def build(self, request: S3PlanningRequest) -> S3PlanningResponse:
        scenario_design = build_s3_scenario_design(
            title=request.title,
            mission_or_training_goal=request.mission_or_training_goal,
            event_type=request.event_type,
            audience=request.audience,
            scenario_archetype=request.scenario_archetype,
            inject_tags=request.inject_tags,
            primary_scenario_input=request.primary_scenario_input,
            secondary_scenario_input=request.secondary_scenario_input,
            current_event_context=request.current_event_context,
            source_items=request.source_items,
            coordinating_sections=request.coordinating_sections,
            constraints=request.constraints,
        )
        met_alignment = _met_alignment(request)
        subordinate_packets = _subordinate_prompt_packets(request)

        mission_analysis = [
            f"Mission / training goal: {request.mission_or_training_goal}",
            f"Event type to plan around: {request.event_type}",
            "Confirm the desired end state, supported commander decision, and what success looks like at close-out.",
            "Separate what must be decided now from what can remain a follow-on action between drills.",
            "Build the smallest event that still trains to a real standard and produces a usable output.",
            "Use the scenario to force decisions, reporting, and adaptation "
            "instead of letting it become background flavor.",
        ]
        if request.audience:
            mission_analysis.append(f"Primary audience / formation: {request.audience}")
        if request.timeframe:
            mission_analysis.append(f"Planning timeframe / window: {request.timeframe}")

        critical_tasks = [
            "Confirm the minimum products and rehearsals needed before execution.",
            "Identify support requests or approvals that sit on the critical path.",
            "Assign owners for tasking, tracking, and after-action capture.",
            "Translate the concept into specific drill-period tasks instead of leaving it as intent only.",
            "Kill nice-to-have activity that burns time without increasing standards or assessment value.",
            "Tie the parent scenario to one friction point that forces subordinate leaders to decide and report.",
        ]
        critical_tasks.extend(f"Constraint to manage: {item}" for item in request.constraints)

        sections = request.coordinating_sections or ["S-1", "S-4", "S-6", "Safety / ORM"]
        coordination_matrix = [
            f"{section}: identify required support, suspense, and decision needed from this section."
            for section in sections
        ]
        coordination_matrix.append(
            "Commander / XO: confirm review point before treating the plan as final."
        )

        battle_rhythm = [
            "Before next drill: gather assumptions, missing information, and support requirements.",
            "At the start of drill: publish the short planning focus, priorities, and suspense list.",
            "During drill: run synchronization checks with supporting sections and capture decisions in writing.",
            "Before execution: conduct one focused backbrief on intent, reporting, and branch conditions.",
            "End of drill: confirm follow-up actions, required products, and owner handoffs before dismissal.",
            "Between drills: track unresolved suspense items and prep the next decision brief.",
        ]

        command_decision_points = [
            "What must the commander approve, prioritize, defer, or cancel?",
            "What support shortfall would force a branch or modified plan?",
            "What risk, timeline, or readiness issue needs command visibility before execution?",
            "What should be cut now so the unit can execute the remaining plan cleanly?",
            "What scenario turn or escalation point should the parent unit control "
            "rather than leave to ad hoc improvisation?",
        ]

        required_outputs = [
            "Short mission analysis / planning note",
            "Task list with owners and suspense dates",
            "Required correspondence or routing products",
            "Simple execution matrix or synchronization board",
            "Training/event support checklist",
            "Scenario inject matrix with branch conditions",
            "AAR capture plan and post-event follow-up list",
        ]

        citations = [item.get("title", "Public-source item") for item in request.source_items[:4]]
        if not citations and request.current_event_context:
            citations.append("User-provided current-event context")
        if not citations:
            citations = ["MCDP 5 Planning", "MCO 1553.3C Unit Training Management"]

        reserve_friction_points = [
            "Limited drill periods compress planning, coordination, and decision time.",
            "Distributed personnel create accountability and comm friction between drills.",
            "Support sections may not all be present at the same time, so handoff discipline matters.",
            "Admin and travel due-outs can quietly displace real operational focus if not separated early.",
            "A good scenario will outrun the unit's control measures if reporting windows and scope are vague.",
        ]

        return S3PlanningResponse(
            title=f"S-3 planning support: {request.title}",
            mission_analysis=mission_analysis,
            scenario_archetype_used=scenario_design.archetype,
            inject_tags_used=scenario_design.inject_tags_used,
            scenario_setting=scenario_design.setting,
            scenario_frame=scenario_design.frame,
            adversary_profile=scenario_design.actors,
            scenario_escalation=scenario_design.escalation,
            narrative_beats=scenario_design.beats,
            injects=[f"{inject.phase}: {inject.title} - {inject.inject}" for inject in scenario_design.injects],
            inject_matrix=scenario_design.injects,
            facilitator_notes=scenario_design.facilitator_notes,
            met_alignment=met_alignment,
            critical_tasks=critical_tasks,
            coordination_matrix=coordination_matrix,
            battle_rhythm=battle_rhythm,
            command_decision_points=command_decision_points,
            required_outputs=required_outputs,
            subordinate_prompt_packets=subordinate_packets,
            citations=citations,
            reserve_friction_points=reserve_friction_points,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "S-3 planning support is advisory only and must be reconciled "
                    "with current command guidance and verified sources."
                ),
            ],
        )


def _met_alignment(request: S3PlanningRequest) -> list[str]:
    items = [f"MET alignment candidate: {task}" for task in request.met_tasks]
    items.extend(f"METL alignment candidate: {task}" for task in request.metl_focus)
    if not items:
        items.append(
            "Manual review required: identify the MET/METL or standard the S-3 package is supposed to sharpen."
        )
    return items


def _subordinate_prompt_packets(request: S3PlanningRequest) -> list[S3SubordinatePromptPacket]:
    if not request.subordinate_units:
        return []
    return [_packet_for_unit(unit, request) for unit in request.subordinate_units]


def _packet_for_unit(
    unit: S3SubordinateUnitInput,
    request: S3PlanningRequest,
) -> S3SubordinatePromptPacket:
    purpose = unit.purpose or (
        f"Support the parent unit's plan for {request.mission_or_training_goal} without drifting from command intent."
    )
    task = (
        f"On order, {unit.unit_name} { _relationship_verb(unit.relationship) } "
        f"the parent training concept and submit a local concept that stays nested with the event standard."
    )
    end_state = (
        f"{unit.unit_name} has a clear local concept, named support shortfalls, required reports, and an AAR lens "
        "before execution begins."
    )
    resource_prompts = [
        "What mobility, communications, accountability, and medical support does this element require?",
        "What can this unit execute with organic capability, and what must be requested early?",
        *[f"Resource bias to account for: {item}" for item in unit.resource_bias[:3]],
    ]
    planning_prompts = [
        "What is this unit's task, purpose, and end state in one clean paragraph?",
        "What report or decision does this unit owe the parent formation first?",
        "What branch condition forces this unit to change tempo, route, or support ask?",
        "What must this unit brief back before the plan is treated as executable?",
    ]
    reporting_requirements = [
        "Initial backbrief of local concept and shortfalls",
        "Execution-status report by phase or control measure",
        "AAR input tied to task, standard, friction, and corrective action",
    ]
    return S3SubordinatePromptPacket(
        unit_name=unit.unit_name,
        relationship=unit.relationship,
        task=task,
        purpose=purpose,
        end_state=end_state,
        resource_prompts=resource_prompts,
        planning_prompts=planning_prompts,
        reporting_requirements=reporting_requirements,
    )


def _relationship_verb(relationship: str) -> str:
    value = relationship.lower()
    if value in {"supporting", "attached"}:
        return "supports"
    if value in {"supported", "main effort"}:
        return "serves as the supported effort for"
    return "executes its portion of"
