from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.schemas.staff_updates import (
    CpbResponse,
    CubResponse,
    LonePlannerResponse,
    MissionAnalysisResponse,
    PlanningCellResponse,
    RunningEstimateItem,
    RunningEstimateRequest,
    RunningEstimateResponse,
    StaffSectionUpdate,
    StaffUpdateCycleResponse,
)
from app.services.planning.approach import assess_planning_approach
from app.services.staff_products.builder import StaffProductBuilder


class StaffUpdateCycleBuilder:
    def __init__(self) -> None:
        self._products = StaffProductBuilder()

    def build_running_estimate(self, request: RunningEstimateRequest) -> RunningEstimateResponse:
        warnings = _warnings_for(request)
        estimates = [_estimate_from_update(update) for update in request.section_updates]
        return RunningEstimateResponse(
            title=f"Running estimate: {request.title}",
            supported_unit=request.supported_unit,
            running_estimates=estimates,
            command_summary=_command_summary(request, estimates),
            warnings=warnings,
        )

    def build_mission_analysis(self, request: RunningEstimateRequest) -> MissionAnalysisResponse:
        warnings = _warnings_for(request)
        assumptions = _unique_ordered(
            [item for update in request.section_updates for item in update.assumptions]
            + [
                "Subordinate and adjacent sections can execute their named due-outs inside the stated planning window."
            ]
        )
        specified_tasks = _specified_tasks(request)
        implied_tasks = _implied_tasks(request)
        essential_tasks = _unique_ordered(
            [
                *specified_tasks[:3],
                *[
                    item for item in implied_tasks
                    if "publish" in item.lower() or "confirm" in item.lower() or "synchronize" in item.lower()
                ][:3],
            ]
        )
        information_requirements = _information_requirements(request)
        staff_estimate_requirements = _staff_estimate_requirements(request)
        commander_decisions = _unique_ordered(
            [item for update in request.section_updates for item in update.decisions_needed]
        )
        command_frame = _unique_ordered(
            [
                f"Purpose: {request.mission_or_training_goal}",
                *([f"Time available: {request.time_available}"] if request.time_available else []),
                *([f"Planning horizon: {request.timeframe}"] if request.timeframe else []),
                *[f"Commander priority: {item}" for item in request.commander_priorities[:4]],
                *[f"Higher guidance: {item}" for item in request.higher_guidance[:3]],
            ]
        )
        return MissionAnalysisResponse(
            title=f"Mission analysis: {request.title}",
            supported_unit=request.supported_unit,
            mission_statement=_mission_statement(request),
            command_frame=command_frame,
            specified_tasks=specified_tasks,
            implied_tasks=implied_tasks,
            essential_tasks=essential_tasks,
            constraints=_unique_ordered(request.constraints),
            assumptions=assumptions,
            information_requirements=information_requirements,
            staff_estimate_requirements=staff_estimate_requirements,
            commander_decisions=commander_decisions,
            warnings=warnings,
        )

    def build_cub(self, request: RunningEstimateRequest) -> CubResponse:
        running_estimate = self.build_running_estimate(request)
        command_snapshot = _cub_snapshot(request, running_estimate.running_estimates)
        commander_decisions = _unique_ordered(
            [item for estimate in running_estimate.running_estimates for item in estimate.decisions_needed]
        )
        due_outs = _due_outs(request, running_estimate.running_estimates)
        friction = _cross_staff_friction(running_estimate.running_estimates)
        brief = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.command_update_brief,
                topic=f"CUB for {request.title}",
                audience=request.supported_unit,
                echelon=request.supported_echelon.value,
                facts=[
                    f"Mission/training goal: {request.mission_or_training_goal}",
                    *[f"Command snapshot: {item}" for item in command_snapshot[:4]],
                    *[f"Decision required: {item}" for item in commander_decisions[:4]],
                    *[f"Cross-staff friction: {item}" for item in friction[:4]],
                    *[f"Due-out: {item}" for item in due_outs[:4]],
                ],
                constraints=[
                    "Keep the CUB focused on what changed, what is blocked, and what the commander/XO needs now."
                ],
                training_or_fictional=request.training_only,
            )
        )
        return CubResponse(
            title=f"CUB package: {request.title}",
            command_snapshot=command_snapshot,
            running_estimates=running_estimate.running_estimates,
            cross_staff_friction=friction,
            commander_decisions=commander_decisions,
            due_outs=due_outs,
            update_brief=brief,
            warnings=running_estimate.warnings,
        )

    def build_cpb(self, request: RunningEstimateRequest) -> CpbResponse:
        running_estimate = self.build_running_estimate(request)
        command_frame = _cpb_frame(request, running_estimate.running_estimates)
        key_assumptions = _unique_ordered(
            [item for estimate in running_estimate.running_estimates for item in estimate.assumptions]
        )
        decision_points = _unique_ordered(
            [item for estimate in running_estimate.running_estimates for item in estimate.decisions_needed]
        )
        branches_and_sequels = _branches_and_sequels(request, running_estimate.running_estimates)
        brief = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.decision_brief,
                topic=f"CPB for {request.title}",
                audience=request.supported_unit,
                echelon=request.supported_echelon.value,
                facts=[
                    f"Mission/training goal: {request.mission_or_training_goal}",
                    *[f"Command frame: {item}" for item in command_frame[:4]],
                    *[f"Decision point: {item}" for item in decision_points[:4]],
                    *[f"Branch or sequel: {item}" for item in branches_and_sequels[:4]],
                ],
                constraints=[
                    "Focus the CPB on decisions, assumptions, and branch planning instead of re-briefing stable detail."
                ],
                training_or_fictional=request.training_only,
            )
        )
        return CpbResponse(
            title=f"CPB package: {request.title}",
            command_frame=command_frame,
            running_estimates=running_estimate.running_estimates,
            key_assumptions=key_assumptions,
            decision_points=decision_points,
            branches_and_sequels=branches_and_sequels,
            command_brief=brief,
            warnings=running_estimate.warnings,
        )

    def build_update_cycle(self, request: RunningEstimateRequest) -> StaffUpdateCycleResponse:
        running_estimate = self.build_running_estimate(request)
        cub = self.build_cub(request)
        cpb = self.build_cpb(request)
        return StaffUpdateCycleResponse(
            title=f"Staff update cycle: {request.title}",
            running_estimate=running_estimate,
            cub=cub,
            cpb=cpb,
            warnings=running_estimate.warnings,
        )

    def build_planning_cell(self, request: RunningEstimateRequest) -> PlanningCellResponse:
        mission_analysis = self.build_mission_analysis(request)
        update_cycle = self.build_update_cycle(request)
        planning_approach = assess_planning_approach(
            title=request.title,
            mission_or_training_goal=request.mission_or_training_goal,
            event_type=request.event_type,
            timeframe=request.time_available or request.timeframe,
            constraints=request.constraints,
            higher_guidance=request.higher_guidance,
            coordinating_sections=request.coordinating_sections,
            support_requirements=request.support_requirements,
            partner_types=request.partner_types,
            civil_considerations=request.civil_considerations,
            subordinate_unit_count=0,
            source_items_present=False,
            formal_event=False,
            raw_guidance_text=None,
        )
        assumption_log = mission_analysis.assumptions
        commander_decision_log = mission_analysis.commander_decisions
        due_out_board = update_cycle.cub.due_outs
        red_team_focus = _unique_ordered(
            [
                *[f"Challenge assumption: {item}" for item in assumption_log[:4]],
                *[f"Stress decision point: {item}" for item in commander_decision_log[:4]],
                *[f"Probe friction: {item}" for item in update_cycle.cub.cross_staff_friction[:4]],
            ]
        )
        next_opt_actions = _unique_ordered(
            [
                "Restate the mission and confirm the commander's planning priority before sliding into product work.",
                "Keep one visible assumption log, one visible decision log, and one due-out board for the staff.",
                *[f"Get a section estimate from: {item}" for item in mission_analysis.staff_estimate_requirements[:4]],
                "Run a red-team check before the commander brief if assumptions or branches are still soft.",
            ]
        )
        return PlanningCellResponse(
            title=f"Planning cell package: {request.title}",
            planning_approach=planning_approach,
            mission_analysis=mission_analysis,
            update_cycle=update_cycle,
            assumption_log=assumption_log,
            commander_decision_log=commander_decision_log,
            due_out_board=due_out_board,
            red_team_focus=red_team_focus,
            next_opt_actions=next_opt_actions,
            warnings=mission_analysis.warnings,
        )

    def build_lone_planner(self, request: RunningEstimateRequest) -> LonePlannerResponse:
        planning_cell = self.build_planning_cell(request)
        sections = _present_sections(request)
        likely_blind_spots = _lone_planner_blind_spots(request, sections)
        missing_section_questions = _lone_planner_questions(request, sections)
        cross_lane_asks = _lone_planner_cross_lane_asks(request, sections)
        recommended_products = _lone_planner_products(request, planning_cell)
        immediate_actions = _unique_ordered(
            [
                *planning_cell.next_opt_actions[:4],
                *[f"Decision now: {item}" for item in planning_cell.commander_decision_log[:3]],
                *[f"Due-out now: {item}" for item in planning_cell.due_out_board[:3]],
            ]
        )
        walk_in_brief = _unique_ordered(
            [
                planning_cell.planning_approach.decision,
                f"Mission statement: {planning_cell.mission_analysis.mission_statement}",
                *(
                    [f"Commander priority: {item}" for item in request.commander_priorities[:2]]
                    if request.commander_priorities
                    else [
                        "Commander priority: Clarify what the commander actually needs "
                        "decided before polishing products."
                    ]
                ),
                *(
                    [f"Assumption that breaks first: {planning_cell.assumption_log[0]}"]
                    if planning_cell.assumption_log
                    else []
                ),
                *(
                    [f"Immediate due-out: {planning_cell.due_out_board[0]}"]
                    if planning_cell.due_out_board
                    else []
                ),
            ]
        )
        posture = (
            "Thin bench, manageable if the staff keeps one visible mission-analysis frame and names owners now."
            if len(sections) >= 3
            else (
                "Thin bench, elevated blind-spot risk. Keep the frame simple and force "
                "missing-section questions early."
            )
        )
        return LonePlannerResponse(
            title=f"Lone planner assist: {request.title}",
            posture=posture,
            walk_in_brief=walk_in_brief,
            likely_blind_spots=likely_blind_spots,
            missing_section_questions=missing_section_questions,
            cross_lane_asks=cross_lane_asks,
            recommended_products=recommended_products,
            immediate_actions=immediate_actions,
            planning_cell=planning_cell,
            warnings=planning_cell.warnings,
        )


def _estimate_from_update(update: StaffSectionUpdate) -> RunningEstimateItem:
    supportability = [
        *[f"Support request: {item}" for item in update.support_requests],
        *[f"Open issue: {item}" for item in update.open_issues[:2]],
    ]
    return RunningEstimateItem(
        section=update.section,
        current_situation=[update.summary],
        changes_since_last=update.changes_since_last,
        assumptions=update.assumptions,
        risks=update.risks or update.open_issues[:2],
        supportability=supportability,
        decisions_needed=update.decisions_needed,
        next_24_72=update.next_24_72,
        asks_of_adjacent_sections=update.adjacent_section_asks,
    )


def _command_summary(
    request: RunningEstimateRequest,
    estimates: list[RunningEstimateItem],
) -> list[str]:
    return _unique_ordered(
        [
            f"{request.supported_unit} is tracking {len(estimates)} section running estimate(s) for {request.title}.",
            *([f"Timeframe: {request.timeframe}"] if request.timeframe else []),
            *[f"Commander priority: {item}" for item in request.commander_priorities[:3]],
            *[f"Higher guidance: {item}" for item in request.higher_guidance[:2]],
            *[f"MET/METL focus: {item}" for item in [*request.met_tasks[:2], *request.metl_focus[:2]]],
        ]
    )


def _cub_snapshot(
    request: RunningEstimateRequest,
    estimates: list[RunningEstimateItem],
) -> list[str]:
    snapshot = [
        f"Purpose: {request.mission_or_training_goal}",
        "Lead the CUB with what changed, what is blocked, and what the commander/XO must decide now.",
    ]
    snapshot.extend(f"{estimate.section}: {estimate.current_situation[0]}" for estimate in estimates[:5])
    snapshot.extend(
        f"{estimate.section} changed: {estimate.changes_since_last[0]}"
        for estimate in estimates
        if estimate.changes_since_last[:1]
    )
    return _unique_ordered(snapshot)


def _cpb_frame(
    request: RunningEstimateRequest,
    estimates: list[RunningEstimateItem],
) -> list[str]:
    frame = [
        f"Mission/training frame: {request.mission_or_training_goal}",
        "Use the CPB to support a decision, branch, sequel, or risk call; do not just repackage the CUB.",
    ]
    frame.extend(f"Commander priority: {item}" for item in request.commander_priorities[:3])
    frame.extend(f"{estimate.section} risk: {estimate.risks[0]}" for estimate in estimates if estimate.risks[:1])
    return _unique_ordered(frame)


def _cross_staff_friction(estimates: list[RunningEstimateItem]) -> list[str]:
    friction: list[str] = []
    for estimate in estimates:
        friction.extend(f"{estimate.section}: {item}" for item in estimate.risks[:2])
        friction.extend(f"{estimate.section} support gap: {item}" for item in estimate.supportability[:1])
    return _unique_ordered(friction)


def _due_outs(
    request: RunningEstimateRequest,
    estimates: list[RunningEstimateItem],
) -> list[str]:
    due_outs: list[str] = []
    for estimate in estimates:
        due_outs.extend(f"{estimate.section}: {item}" for item in estimate.next_24_72[:2])
        due_outs.extend(
            f"{estimate.section} owes adjacent staff: {item}"
            for item in estimate.asks_of_adjacent_sections[:1]
        )
    if not due_outs:
        due_outs.append(
            f"{request.supported_unit}: publish the next staff sync update "
            "and confirm section due-outs before the next touchpoint."
        )
    return _unique_ordered(due_outs)


def _branches_and_sequels(
    request: RunningEstimateRequest,
    estimates: list[RunningEstimateItem],
) -> list[str]:
    branches = [
        (
            "If a critical support or reporting assumption fails, shift to the "
            "reduced-scope branch before burning execution time."
        ),
        (
            "If section updates show stable supportability, preserve the current concept "
            "and use the CPB to decide where to accept friction."
        ),
    ]
    if request.met_tasks or request.metl_focus:
        branches.append("Use MET/METL alignment to decide what can be cut without hollowing out the training value.")
    for estimate in estimates:
        if estimate.risks:
            branches.append(
                f"If {estimate.section.lower()} friction worsens, build a sequel "
                f"focused on {estimate.risks[0].lower()}."
            )
    return _unique_ordered(branches)


def _warnings_for(request: RunningEstimateRequest) -> list[str]:
    text = " ".join(
        [
            request.title,
            request.supported_unit,
            request.mission_or_training_goal,
            request.event_type,
            request.time_available or "",
            *request.higher_guidance,
            *request.constraints,
            *request.commander_priorities,
            *[update.summary for update in request.section_updates],
        ]
    )
    return sorted(
        set(
            [
                *DEFAULT_WARNINGS,
                *detect_sensitive_input(text),
                "Running estimates, CUBs, and CPBs are advisory staff products and require human review before use.",
            ]
        )
    )


def _present_sections(request: RunningEstimateRequest) -> set[str]:
    sections = {item.section.strip().lower() for item in request.section_updates if item.section.strip()}
    sections.update(item.strip().lower() for item in request.coordinating_sections if item.strip())
    return sections


def _has_section(sections: set[str], *candidates: str) -> bool:
    normalized = [candidate.lower() for candidate in candidates]
    return any(candidate in section for section in sections for candidate in normalized)


def _lone_planner_blind_spots(request: RunningEstimateRequest, sections: set[str]) -> list[str]:
    blind_spots = [
        "The lone planner should assume at least one adjacent section owes context that is still unstated.",
    ]
    if not _has_section(sections, "s-1", "admin"):
        blind_spots.append(
            "S-1/Admin blind spot: attendance, orders coverage, and admin readiness "
            "may be softer than the concept assumes."
        )
    if not _has_section(sections, "s-4", "log"):
        blind_spots.append(
            "S-4 blind spot: transport, chow, water, issue/recovery, and timing friction "
            "may break the plan first."
        )
    if not _has_section(sections, "s-6", "comm"):
        blind_spots.append(
            "S-6 blind spot: the plan may be assuming reporting or access discipline "
            "that no one has verified."
        )
    if not _has_section(sections, "medical", "corpsman", "doc"):
        blind_spots.append(
            "Medical blind spot: casualty response, stop-training criteria, and coverage "
            "may still be implied instead of checked."
        )
    if not request.section_updates:
        blind_spots.append(
            "No section updates were provided, so the concept is at risk of sounding "
            "cleaner than the staff reality."
        )
    if request.partner_types or request.civil_considerations:
        blind_spots.append(
            "Outside actors or civil considerations are in play; do not let the staff "
            "stay Marine-only in its assumptions."
        )
    return _unique_ordered(blind_spots)


def _lone_planner_questions(request: RunningEstimateRequest, sections: set[str]) -> list[str]:
    questions = [
        "What decision does the commander actually need before the next sync or brief?",
        "Which assumption is most likely to fail first once execution starts?",
    ]
    if not _has_section(sections, "s-1", "admin"):
        questions.append(
            "S-1/Admin: Who is actually attending, covered by orders, and clear on "
            "reporting/accountability expectations?"
        )
    if not _has_section(sections, "s-4", "log"):
        questions.append(
            "S-4: What support timeline, transport, billeting, water, or issue/recovery "
            "fact is still assumed instead of confirmed?"
        )
    if not _has_section(sections, "s-6", "comm"):
        questions.append(
            "S-6: What is the simplest reporting method, and what access or comms "
            "friction will hit the unit first?"
        )
    if not _has_section(sections, "xo", "chief"):
        questions.append(
            "XO/Chief: What can wait, what must be decided now, and what should never "
            "be allowed to drift into a last-minute surprise?"
        )
    if not _has_section(sections, "sel", "first sergeant", "sergeant major"):
        questions.append(
            "SEL/1stSgt: What friction will hit Marines first when the plan meets real "
            "arrival times, gear reality, and accountability?"
        )
    return _unique_ordered(questions)


def _lone_planner_cross_lane_asks(request: RunningEstimateRequest, sections: set[str]) -> list[str]:
    asks = []
    if not _has_section(sections, "s-1", "admin"):
        asks.append(
            "Ask S-1/Admin for a blunt attendance, orders, and readiness read instead "
            "of a generic admin comfort statement."
        )
    if not _has_section(sections, "s-4", "log"):
        asks.append(
            "Ask S-4 for the one support assumption that breaks the concept first and "
            "the no-regret fallback if it fails."
        )
    if not _has_section(sections, "s-6", "comm"):
        asks.append(
            "Ask S-6 for one primary reporting method, one fallback, and the access "
            "problem most likely to slow execution."
        )
    if not _has_section(sections, "medical", "corpsman", "doc"):
        asks.append(
            "Ask medical support what stop-training criteria, casualty movement plan, "
            "and med coverage are actually in place."
        )
    asks.append(
        "Ask the XO/Chief to restate the decision threshold: what must be briefed up "
        "now versus what can be carried as a due-out."
    )
    asks.append(
        "Ask the SEL what part of the plan Marines will actually feel first when the "
        "schedule slips or support arrives late."
    )
    if request.partner_types or request.civil_considerations:
        asks.append(
            "Ask who owns outside coordination so partner or civil assumptions do not "
            "hide inside the main scheme of maneuver."
        )
    return _unique_ordered(asks)


def _lone_planner_products(request: RunningEstimateRequest, planning_cell: PlanningCellResponse) -> list[str]:
    products = [
        "Mission analysis worksheet",
        "Planning cell package with visible assumption, decision, and due-out logs",
        "Command update brief / CUB",
        "Decision brief / CPB",
        "Battle rhythm board entry",
    ]
    if planning_cell.commander_decision_log:
        products.append("Commander decision list")
    if request.higher_guidance or planning_cell.update_cycle.cub.due_outs:
        products.append("Short FRAGO or tasking note")
    if request.support_requirements or _has_section(_present_sections(request), "s-1", "admin", "s-4", "log"):
        products.append("Admin readiness and supportability check")
    return _unique_ordered(products)


def _unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _mission_statement(request: RunningEstimateRequest) -> str:
    supported = request.supported_unit
    purpose = request.mission_or_training_goal.rstrip(".")
    return (
        f"{supported} conducts planning for {request.title} in order to {purpose.lower()} "
        "while preserving supportability, standards, and an assessable output."
    )


def _specified_tasks(request: RunningEstimateRequest) -> list[str]:
    tasks = []
    for item in request.higher_guidance:
        tasks.append(item)
    for item in request.commander_priorities[:2]:
        tasks.append(f"Protect this commander priority: {item}")
    if request.met_tasks:
        tasks.extend(f"Keep this MET-aligned task visible: {item}" for item in request.met_tasks[:2])
    if not tasks:
        tasks.append("Clarify the supported event and the commander's required output.")
    return _unique_ordered(tasks)


def _implied_tasks(request: RunningEstimateRequest) -> list[str]:
    tasks = [
        "Publish a shared mission-analysis frame before the staff starts polishing products.",
        "Name section owners, due-outs, and adjacent-section asks before the next sync.",
    ]
    if request.coordinating_sections:
        tasks.extend(f"Pull a usable estimate from {section}." for section in request.coordinating_sections[:5])
    if request.support_requirements:
        tasks.extend(f"Confirm support requirement: {item}" for item in request.support_requirements[:4])
    if request.section_updates:
        tasks.append("Capture what changed since the last update instead of re-briefing stable detail.")
    return _unique_ordered(tasks)


def _information_requirements(request: RunningEstimateRequest) -> list[str]:
    items = [
        "What assumption, if wrong, will break the concept first?",
        "What support or timing fact still needs confirmation before execution?",
    ]
    if request.partner_types or request.civil_considerations:
        items.append("What outside actor or civil consideration could change the plan?")
    if request.metl_focus:
        items.append("What standard or MET/METL lens is this plan supposed to sharpen?")
    items.extend(f"Need from staff: {item}" for item in request.coordinating_sections[:4])
    return _unique_ordered(items)


def _staff_estimate_requirements(request: RunningEstimateRequest) -> list[str]:
    requirements = [update.section for update in request.section_updates]
    requirements.extend(request.coordinating_sections)
    if "XO" not in {item.upper() for item in requirements}:
        requirements.append("XO")
    return _unique_ordered(requirements)
