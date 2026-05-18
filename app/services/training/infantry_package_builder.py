from app.core.security import DEFAULT_WARNINGS
from app.schemas.training import InfantryTrainingPackageRequest, InfantryTrainingPackageResponse
from app.services.agents.source_refs import INFANTRY_REFERENCES, citation_titles


class InfantryTrainingPackageBuilder:
    def build(self, request: InfantryTrainingPackageRequest) -> InfantryTrainingPackageResponse:
        training_frame = [
            f"Training goal: {request.training_goal}",
            (
                "Keep this as a training-safe infantry familiarization package, not a fake advanced 03xx "
                "certification event."
            ),
            (
                f"Primary training population: {request.primary_training_population}. "
                "Build the event for Marines who need exposure, confidence, discipline, and repetition "
                "more than flashy complexity."
            ),
            (
                f"Venue assumption: {request.venue_type}. Ammunition assumption: {request.ammunition_type}. "
                "Use the urban site to teach movement, communication, accountability, and leader control under stress."
            ),
        ]
        if request.unit_name:
            training_frame.append(f"Unit context: {request.unit_name}")
        if request.audience:
            training_frame.append(f"Audience: {request.audience}")
        if request.training_window:
            training_frame.append(f"Training window to plan around: {request.training_window}")

        recommended_scope = [
            (
                "Do one modified lane well instead of pretending a support/admin population is ready for "
                "an advanced urban package."
            ),
            (
                "Keep the package at team and small-squad discipline level: movement, sectors, reports, "
                "casualty control, and simple problem-solving."
            ),
            (
                "Use blanks to reinforce command-and-control, weapons status, accountability, and leader "
                "presence, not cinematic room-clearing."
            ),
            (
                "Treat this as a familiarization and confidence-building event nested under 03xx "
                "fundamentals, not a substitute for formal infantry progression."
            ),
        ]
        recommended_scope.extend(f"Constraint to respect: {item}" for item in request.constraints[:4])

        training_phases = [
            (
                "Phase I - prep and orientation: safety brief, blank-fire controls, lane walk-through, "
                "and common vocabulary."
            ),
            (
                "Phase II - dry repetitions: movement, sectors, entry/exit control measures, reporting, "
                "casualty actions, and leader positioning with no ammunition."
            ),
            (
                "Phase III - blank-fire iterations: one simple urban lane with observer/controllers "
                "enforcing pace, comm, and accountability."
            ),
            (
                "Phase IV - friction inject: degraded report, simulated casualty, or leader-loss inject "
                "that forces control and branch thinking."
            ),
            (
                "Phase V - AAR and retrain: repeat the weakest portion immediately after feedback instead "
                "of saving all learning for the final wrap-up."
            ),
        ]

        lane_design = [
            (
                "Start outside the structure and force accountability, task organization, and "
                "weapons-condition discipline before movement."
            ),
            (
                "Give each team one clean task and one clear report requirement so the lane measures "
                "control, not improvisation theater."
            ),
            (
                "Use obvious control measures inside the urban site: checkpoints, decision points, "
                "casualty point, and stop-training boundary."
            ),
            (
                "Limit the first lane to a small number of rooms/structures or one short street problem "
                "so supervision stays honest."
            ),
            (
                "Add one simple urban friction point: blocked route, missed report, separated Marine, "
                "or casualty drag requirement."
            ),
        ]

        prerequisite_materials = [
            "MCWP 3-10 MAGTF Ground Operations for overall GCE framing.",
            "MCWP 3-01 Offensive and Defensive Tactics for basic tactical vocabulary.",
            "MCRP 3-10A.2 / 3-10A.3 / 3-10A.4 for company, platoon, and squad context.",
            "MCTP 12-10B Urban Operations for urban problem framing and training context.",
            "NAVMC 3500.44D and NAVMC 3500.18D to anchor standards and evaluation language.",
            "Local range/facility SOP, blank-fire SOP, medical plan, and safety controls before execution.",
        ]

        leader_rehearsals = [
            "Rehearse lane control, cease-training criteria, and who can freeze the iteration immediately.",
            (
                "Rehearse observer/controller positions and what they are grading: control, "
                "communication, accountability, and safety."
            ),
            (
                "Rehearse casualty response, blank-fire malfunction/control calls, and end-of-lane "
                "weapons clearing sequence."
            ),
            "Confirm the exact standard for what gets corrected on the spot versus what waits for the AAR.",
        ]

        blank_fire_controls = [
            "Use local blank-fire SOP and qualified safety oversight; this package does not replace local procedures.",
            (
                "Confirm approved weapons condition, magazine/loading sequence, blank-adapter checks, "
                "and clearing procedures before first rep."
            ),
            "Control muzzle awareness, safe separation, and no-fire / no-move boundaries inside the urban site.",
            (
                "Stage ammo issue, turn-in, and accountability so supervision is strongest at "
                "transitions, not just at start and finish."
            ),
            "Cut complexity immediately if inexperience, fatigue, or supervision gaps start outrunning the controls.",
        ]

        orm_controls = [
            "No-go if qualified supervision, medical response, or local SOP alignment is weak.",
            "Reduce scope if Marines do not demonstrate basic movement and weapons discipline during dry runs.",
            (
                "Plan heat, hydration, trip hazards, noise, visibility, and building-clearance controls "
                "around the actual site."
            ),
            (
                "Separate training value from ego: if the event starts looking like performative CQB "
                "instead of controlled learning, scale it back."
            ),
        ]
        orm_controls.extend(f"Support dependency to verify: {item}" for item in request.support_requirements[:4])

        evaluation_points = [
            "Did leaders maintain control, pace, and accountability from start to finish?",
            "Were reports timely, understandable, and tied to decision points in the lane?",
            "Did Marines maintain weapons-status and blank-fire discipline during movement and transitions?",
            "Could the team handle one friction point without losing control of the whole lane?",
            "Did the retrain iteration fix the actual weak point from the first rep?",
        ]
        evaluation_points.extend(f"MET alignment candidate: {item}" for item in request.met_tasks)
        evaluation_points.extend(f"METL alignment candidate: {item}" for item in request.metl_focus)

        aar_prompts = [
            "What part of the package actually built confidence and discipline, and what was just noise?",
            (
                "Where did leader control break down first: movement, reports, accountability, "
                "casualty actions, or safety transitions?"
            ),
            "What should be kept as the baseline familiarization lane for future non-03 Marines?",
            "What must be retrained before any attempt to make the lane more complex next time?",
        ]

        return InfantryTrainingPackageResponse(
            title=f"03 familiarization package: {request.title}",
            training_frame=training_frame,
            recommended_scope=recommended_scope,
            training_phases=training_phases,
            lane_design=lane_design,
            prerequisite_materials=prerequisite_materials,
            leader_rehearsals=leader_rehearsals,
            blank_fire_controls=blank_fire_controls,
            orm_controls=orm_controls,
            evaluation_points=evaluation_points,
            aar_prompts=aar_prompts,
            citations=citation_titles(INFANTRY_REFERENCES),
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "This infantry familiarization package is advisory and training-only. It does not replace "
                    "qualified 03xx leaders, local blank-fire SOP, OIC/RSO review, or command approval."
                ),
            ],
        )
