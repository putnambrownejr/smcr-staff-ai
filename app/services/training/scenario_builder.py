from __future__ import annotations

from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import (
    RangeSafetyRequest,
    RangeSafetyResponse,
    TrainingScenarioRequest,
    TrainingScenarioResponse,
    TrainingScenarioType,
)
from app.services.training.scenario_engine import build_s3_scenario_design


class TrainingScenarioBuilder:
    def build(self, request: TrainingScenarioRequest) -> TrainingScenarioResponse:
        concept, support_requirements, admin_requirements, orm_considerations = _scenario_parts(request.scenario_type)
        concept = [f"Objective: {request.training_objective}", *concept]
        if request.audience:
            concept.append(f"Audience: {request.audience}")
        scenario_design = build_s3_scenario_design(
            title=request.title,
            mission_or_training_goal=request.training_objective,
            event_type=request.scenario_type.value,
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
        concept.extend(
            [
                "Use a fictionalized but recognizable conflict logic rather than a generic good-guys/bad-guys setup.",
                "Keep the adversary name fictional, but make the environment, friction, and escalation feel plausible.",
            ]
        )
        admin_requirements.extend(f"Constraint to account for: {item}" for item in request.constraints)
        return TrainingScenarioResponse(
            title=f"{request.scenario_type.value.replace('_', ' ').title()} scenario: {request.title}",
            scenario_type=request.scenario_type,
            scenario_archetype_used=scenario_design.archetype,
            inject_tags_used=scenario_design.inject_tags_used,
            concept=concept,
            scenario_setting=scenario_design.setting,
            adversary_profile=scenario_design.actors,
            narrative_beats=scenario_design.beats,
            inject_matrix=scenario_design.injects,
            facilitator_notes=scenario_design.facilitator_notes,
            support_requirements=support_requirements,
            admin_requirements=admin_requirements,
            orm_considerations=orm_considerations,
            aar_prompts=[
                "What training objective was met or missed?",
                "What sustain/improve items should be captured with owners and suspense dates?",
                "What admin or safety friction should be corrected before the next event?",
            ],
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Training scenario support is for fictional/training-only use "
                    "unless handled in an approved environment."
                ),
            ],
        )


class RangeSafetyBuilder:
    def build(self, request: RangeSafetyRequest) -> RangeSafetyResponse:
        required_admin = [
            "Range request / coordination record",
            "Ammo and weapon system support plan",
            "Medical / CASEVAC support confirmation",
            "Transportation and accountability plan",
        ]
        if request.range_type:
            required_admin.append(f"Range type to verify against local SOP: {request.range_type}")
        if request.weapon_systems:
            required_admin.append("Weapon systems in scope: " + ", ".join(request.weapon_systems))
        if request.ammunition:
            required_admin.append("Ammunition in scope: " + ", ".join(request.ammunition))
        if not request.live_fire:
            required_admin.append(
                "This appears dry or simulation-focused; still verify local handling, supervision, and control "
                "measures."
            )
        return RangeSafetyResponse(
            title=f"Range safety support: {request.event_name}",
            required_roles=["OIC", "RSO", "corpsman / medical support", "ammo / transport support"],
            required_admin=required_admin,
            orm_controls=[
                "Identify hazards by firing line, movement, weather, ammunition handling, and personnel inexperience.",
                "Confirm communications, cease-fire procedures, weapons conditions, and emergency actions before "
                "first iteration.",
                "Assign supervision, residual-risk owner, and accountability checks for each transition, not just "
                "the firing line.",
                "Rehearse the step that is most likely to get rushed when the schedule slips.",
            ],
            no_go_criteria=[
                "Do not execute if qualified OIC/RSO coverage is unclear or not present.",
                "Do not execute if medical response, evacuation path, or casualty transport plan is unresolved.",
                "Do not execute if cease-fire authority, weapons status procedures, or ammo accountability are vague.",
                "Do not execute if local range-control restrictions, weather, or visibility conditions are unverified.",
            ],
            leader_verification_questions=[
                "What condition would cause the OIC or RSO to reduce scope rather than force the event through?",
                "Which transition is most likely to generate a negligent discharge or accountability lapse if rushed?",
                "Who can stop training immediately, and does everyone know that by role and sequence?",
                "Which safety assumption depends on local SOP or range-control approval instead of staff optimism?",
            ],
            aar_prompts=[
                "Which safety controls worked because they were rehearsed, not improvised?",
                "Where did supervision, weapons status, or line control become ambiguous under time pressure?",
                "What near-miss, friction, or admin issue should be fixed before the next live event?",
            ],
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Range/RSO support is advisory only and must not replace qualified "
                    "range safety oversight or local SOP."
                ),
            ],
        )


def _scenario_parts(
    scenario_type: TrainingScenarioType,
) -> tuple[list[str], list[str], list[str], list[str]]:
    if scenario_type == TrainingScenarioType.range:
        return (
            ["Build a training flow from rehearsal through execution and AAR."],
            ["Range access", "weapons/ammo support", "medical support", "transportation"],
            ["Orders/admin support", "roster/accountability", "travel if required"],
            ["Weapons handling", "medical response", "weather/environment controls"],
        )
    if scenario_type == TrainingScenarioType.annual_training:
        return (
            ["Frame the AT event as a phased reserve-support problem with pre-AT prep, execution, and recovery."],
            ["Billeting", "transportation", "comm support", "training-area or facility support"],
            ["Orders/admin support", "travel and DTS continuity", "roster and readiness tracking"],
            ["Movement and travel", "medical support", "equipment accountability", "leader continuity"],
        )
    if scenario_type == TrainingScenarioType.staff_drill:
        return (
            ["Frame the decision problem, injects, timeline, and expected staff products."],
            ["Facilitator", "inject matrix", "reference products", "AAR capture"],
            ["Orders / drill admin support", "battle rhythm", "attendance / accountability"],
            ["Information management", "role clarity", "time pressure and supervision"],
        )
    if scenario_type == TrainingScenarioType.pme:
        return (
            ["Set learning objective, discussion format, and assessment method."],
            ["Read-ahead material", "discussion prompts", "facilitator notes"],
            ["Attendance tracking", "PME completion note", "follow-up reading list"],
            ["Classroom / venue considerations", "time management", "participation controls"],
        )
    if scenario_type == TrainingScenarioType.civil_support:
        return (
            ["Define the scenario context, stakeholders, and decision points."],
            ["Public-source context", "facilitator injects", "communications support"],
            ["Tasking/admin note", "travel/admin support if distributed personnel are involved"],
            ["Partner coordination", "public information handling", "continuity between drills"],
        )
    return (
        ["Build phases from prep, rehearsal, execution, and recovery."],
        ["Training area", "communications", "logistics support", "AAR capture"],
        ["Orders/admin support", "transportation", "medical readiness check"],
        ["Weather", "movement", "medical support", "supervision and residual-risk ownership"],
    )
