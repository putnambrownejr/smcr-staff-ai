from __future__ import annotations

from app.schemas.fitness import (
    FitnessObjective,
    OrmHazard,
    OrmMatrix,
    PtBlock,
    StaffPtReview,
    UnitPtPlan,
    UnitPtPlanRequest,
)

_SOURCES = [
    "USMC Human Performance Branch — https://www.fitness.marines.mil/",
    "MCO 6100.14 Marine Corps Physical Fitness Program",
    "MCO 1500.62 Force Fitness Instructor Program",
    "MCO 6110.3A W/ADMIN CH-4 Marine Corps Body Composition and Military Appearance Program",
]


def build_unit_pt_plan(request: UnitPtPlanRequest) -> UnitPtPlan:
    band, organization = _organization(request.participant_count)
    blocks = _blocks(request)
    cadence = None
    if request.include_cadence:
        cadence = request.cadence_preference or "Choose a clean cadence from the local cadence library."

    staff_reviews = [
        StaffPtReview(
            role="S-3 / OpsO",
            findings=[
                f"Event supports {request.objective.value} for {request.participant_count} Marines.",
                "Confirm the event fits the training schedule and current commander guidance.",
            ],
            actions=["Publish task, conditions, standard, timeline, and cancellation criteria."],
        ),
        StaffPtReview(
            role="S-4",
            findings=[
                f"Planned equipment: {', '.join(request.equipment) if request.equipment else 'bodyweight only'}.",
                f"Location: {request.location}.",
            ],
            actions=["Confirm water, sanitation, first-aid access, equipment condition, and site permissions."],
        ),
        StaffPtReview(
            role="SgtMaj / SEL",
            findings=[
                "Use visible lane/station leaders and standards that preserve dignity across ability levels.",
                f"Ability input: {request.ability_notes}.",
            ],
            actions=["Brief accountability, form standards, scaling, cadence suitability, and stop-work authority."],
        ),
        StaffPtReview(
            role="ORM",
            findings=["Risk matrix includes heat/cold, injury, traffic/site, accountability, and equipment hazards."],
            actions=["Reassess conditions immediately before execution; route residual-risk acceptance properly."],
        ),
        StaffPtReview(
            role="Fitness / FFI coordination",
            findings=["This tool is not an FFI, CPTR, medical provider, or official PFT/CFT monitor."],
            actions=["Have qualified personnel validate official events and individual medical restrictions."],
        ),
    ]
    return UnitPtPlan(
        participant_count=request.participant_count,
        scaling_band=band,
        objective=request.objective,
        duration_minutes=request.duration_minutes,
        organization=organization,
        blocks=blocks,
        cadence=cadence,
        staff_reviews=staff_reviews,
        orm=_orm(request),
        warnings=[
            "Training draft only; confirm current orders, local policy, qualified supervision, and medical restrictions.",
            "Do not use this planner to diagnose injury, prescribe rehabilitation, or certify an official PFT/CFT.",
            "Weather and site conditions are user-provided and may be stale; reassess immediately before execution.",
        ],
        sources=_SOURCES,
    )


def _organization(count: int) -> tuple[str, list[str]]:
    if count <= 12:
        return "small element (5–12)", ["One formation", "One lead trainer", "One safety/accountability Marine"]
    if count <= 24:
        return "two-lane element (13–24)", ["Two balanced lanes", "One leader per lane", "One overall safety lead"]
    return (
        "station element (25–50)",
        ["Four stations", "One leader per station", "Staggered starts", "One overall OIC and one safety lead"],
    )


def _blocks(request: UnitPtPlanRequest) -> list[PtBlock]:
    warmup = max(8, round(request.duration_minutes * 0.18))
    cooldown = max(5, round(request.duration_minutes * 0.12))
    main = request.duration_minutes - warmup - cooldown
    focus = {
        FitnessObjective.pft: "pull-up/push-up, plank, and aerobic intervals",
        FitnessObjective.cft: "movement-to-contact intervals, lift/carry technique, and maneuver-under-fire patterns",
        FitnessObjective.strength: "controlled compound bodyweight or available-equipment strength stations",
        FitnessObjective.endurance: "progressive aerobic intervals with ability-based pace groups",
        FitnessObjective.mobility: "controlled mobility, easy aerobic work, and recovery-focused movement",
        FitnessObjective.general: "balanced strength, movement quality, and aerobic conditioning",
    }[request.objective]
    return [
        PtBlock(
            name="Accountability, brief, and dynamic warm-up",
            minutes=warmup,
            instructions=["Confirm accountability and limitations.", "Demonstrate movements before adding speed."],
            scaling=["Reduce range or pace before sacrificing form.", "Provide a low-impact lane."],
        ),
        PtBlock(
            name="Main training block",
            minutes=main,
            instructions=[f"Emphasize {focus}.", "Use work/rest intervals visible to every lane or station."],
            scaling=["Use effort bands: foundational, standard, advanced.", "Never use exercise as punishment."],
        ),
        PtBlock(
            name="Cooldown and accountability",
            minutes=cooldown,
            instructions=["Return to easy movement, hydrate as appropriate, and recheck accountability."],
            scaling=["Allow individual movement restrictions and qualified medical guidance to control."],
        ),
    ]


def _orm(request: UnitPtPlanRequest) -> OrmMatrix:
    environment = request.weather_notes or "conditions not supplied"
    return OrmMatrix(
        hazards=[
            OrmHazard(
                hazard=f"Heat, cold, or severe weather ({environment})",
                initial_risk="high",
                controls=[
                    "Check current official weather guidance",
                    "Set hydration/work-rest plan",
                    "Use acclimatization and cancellation criteria",
                ],
                residual_risk="medium",
                owner="OIC / safety lead",
                stop_trigger="Heat/cold injury signs, lightning, or conditions exceeding current local policy",
            ),
            OrmHazard(
                hazard="Musculoskeletal injury or unreported limitation",
                initial_risk="high",
                controls=["Dynamic warm-up", "Demonstrate form", "Ability-based scaling", "Honor medical limitations"],
                residual_risk="medium",
                owner="Lane/station leaders",
                stop_trigger="Pain, altered gait/form, dizziness, or participant requests stop",
            ),
            OrmHazard(
                hazard=f"Site, traffic, or surface at {request.location}",
                initial_risk="medium",
                controls=["Walk the site", "Mark boundaries", "Control vehicle interaction", "Maintain communications"],
                residual_risk="low",
                owner="S-3 / site lead",
                stop_trigger="Unauthorized traffic, unsafe surface, lost communications, or boundary breach",
            ),
            OrmHazard(
                hazard="Accountability across lanes or stations",
                initial_risk="medium",
                controls=["Roster/count before and after", "Named leaders", "Buddy checks", "Central muster point"],
                residual_risk="low",
                owner="SgtMaj / SEL representative",
                stop_trigger="Unaccounted Marine or uncontrolled group movement",
            ),
            OrmHazard(
                hazard="Damaged or unsuitable equipment",
                initial_risk="medium" if request.equipment else "low",
                controls=["Inspect before use", "Remove failed equipment", "Maintain bodyweight alternate"],
                residual_risk="low",
                owner="S-4 / station leader",
                stop_trigger="Equipment failure or unsafe setup",
            ),
        ]
    )
