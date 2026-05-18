from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.schemas.staff_updates import (
    CpbResponse,
    CubResponse,
    RunningEstimateItem,
    RunningEstimateRequest,
    RunningEstimateResponse,
    StaffSectionUpdate,
    StaffUpdateCycleResponse,
)
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
            *request.higher_guidance,
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
