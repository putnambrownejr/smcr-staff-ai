from __future__ import annotations

from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import (
    RangeSafetyRequest,
    RangeSafetyResponse,
    TrainingScenarioRequest,
    TrainingScenarioResponse,
    TrainingScenarioType,
)


class TrainingScenarioBuilder:
    def build(self, request: TrainingScenarioRequest) -> TrainingScenarioResponse:
        concept, support_requirements, admin_requirements, orm_considerations = _scenario_parts(request.scenario_type)
        concept = [f"Objective: {request.training_objective}", *concept]
        if request.audience:
            concept.append(f"Audience: {request.audience}")
        admin_requirements.extend(f"Constraint to account for: {item}" for item in request.constraints)
        return TrainingScenarioResponse(
            title=f"{request.scenario_type.value.replace('_', ' ').title()} scenario: {request.title}",
            scenario_type=request.scenario_type,
            concept=concept,
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
        if request.weapon_systems:
            required_admin.append("Weapon systems in scope: " + ", ".join(request.weapon_systems))
        if request.ammunition:
            required_admin.append("Ammunition in scope: " + ", ".join(request.ammunition))
        return RangeSafetyResponse(
            title=f"Range safety support: {request.event_name}",
            required_roles=["OIC", "RSO", "corpsman / medical support", "ammo / transport support"],
            required_admin=required_admin,
            orm_controls=[
                "Identify hazards by firing line, movement, weather, and ammo handling.",
                "Confirm communications, cease-fire procedures, and emergency actions.",
                "Assign supervision, residual-risk owner, and accountability checks.",
            ],
            aar_prompts=[
                "What safety controls worked as planned?",
                "What near-miss, friction, or admin issue should be captured for follow-up?",
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
