from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.planning import (
    PlanningApproachAssessment,
    StaffPlanningPackageRequest,
    StaffPlanningPackageResponse,
)
from app.schemas.staff import (
    CommandCellRequest,
    CommandCellResponse,
    G9PlanningRequest,
    MedicalPlanningRequest,
    MedicalPlanningResponse,
    S1ReadinessRequest,
    S1ReadinessResponse,
    S2EstimateRequest,
    S2EstimateResponse,
    S6PlanRequest,
    S6PlanResponse,
    SafetyPlanningRequest,
    SafetyPlanningResponse,
    SelExecutionRequest,
    SelExecutionResponse,
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffEchelon,
    XoSyncRequest,
    XoSyncResponse,
)
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.schemas.training import S3PlanningRequest, S3PlanningResponse, S4PlanningRequest, S4PlanningResponse
from app.services.planning.approach import assess_planning_approach
from app.services.staff.command_cell_planner import CommandCellPlanner
from app.services.staff.council import StaffCouncilService
from app.services.staff.g9_planner import G9Planner
from app.services.staff.medical_planner import MedicalPlanner
from app.services.staff.s1_readiness_planner import S1ReadinessPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff.safety_planner import SafetyPlanner
from app.services.staff.sel_execution_planner import SelExecutionPlanner
from app.services.staff.xo_sync_planner import XoSyncPlanner
from app.services.staff_products.builder import StaffProductBuilder
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner


class StaffPlanningOrchestrator:
    def __init__(self) -> None:
        self._s2 = S2Estimator()
        self._s3 = S3Planner()
        self._s4 = S4Planner()
        self._s6 = S6Planner()
        self._xo = XoSyncPlanner()
        self._command_cell = CommandCellPlanner()
        self._s1 = S1ReadinessPlanner()
        self._safety = SafetyPlanner()
        self._sel = SelExecutionPlanner()
        self._medical = MedicalPlanner()
        self._g9 = G9Planner()
        self._council = StaffCouncilService()
        self._products = StaffProductBuilder()

    def build(self, request: StaffPlanningPackageRequest) -> StaffPlanningPackageResponse:
        boundary_warnings = detect_sensitive_input(_request_text(request))
        if boundary_warnings:
            request = _sanitize_staff_package_request(request)
        planning_approach = assess_planning_approach(
            title=request.title,
            mission_or_training_goal=request.mission_or_training_goal,
            event_type=request.event_type,
            timeframe=request.timeframe,
            constraints=request.constraints,
            higher_guidance=[],
            coordinating_sections=request.coordinating_sections,
            support_requirements=request.support_requirements,
            partner_types=request.partner_types,
            civil_considerations=request.civil_considerations,
            subordinate_unit_count=0,
            source_items_present=bool(request.source_items or request.intelligence_question),
        )
        s2_estimate = self._build_s2_estimate(request)
        s3_plan = self._s3.build(
            S3PlanningRequest(
                title=request.title,
                mission_or_training_goal=request.mission_or_training_goal,
                event_type=request.event_type,
                audience=request.audience,
                timeframe=request.timeframe,
                constraints=request.constraints,
                coordinating_sections=request.coordinating_sections,
                training_only=request.training_only,
            )
        )
        s4_plan = self._s4.build(
            S4PlanningRequest(
                title=request.title,
                supported_event=request.event_type,
                support_objective=request.support_objective
                or "Support the event with movement, sustainment, accountability, and recovery.",
                audience=request.audience,
                travel_required=_has_travel_indicator(request),
                overnight=_has_overnight_indicator(request),
                constraints=request.constraints,
                support_requirements=request.support_requirements,
            )
        )
        s6_plan = self._s6.build(
            S6PlanRequest(
                title=request.title,
                supported_event=request.event_type,
                c2_objective=request.c2_objective
                or "Support leader coordination, accountability, reporting, and emergency communications.",
                audience=request.audience,
                constraints=request.constraints,
                support_requirements=request.support_requirements,
                training_only=request.training_only,
            )
        )
        xo_sync = self._xo.build(
            XoSyncRequest(
                title=request.title,
                supported_event=request.event_type,
                command_focus=request.mission_or_training_goal,
                audience=request.audience,
                coordinating_sections=request.coordinating_sections,
                critical_decisions=_commander_decisions(request, s3_plan, s4_plan)[:4],
                due_outs=[
                    *s3_plan.required_outputs[:2],
                    *s4_plan.coordination_points[:2],
                    *s6_plan.comm_plan_outline[:1],
                ],
                constraints=request.constraints,
                training_only=request.training_only,
            )
        )
        command_cell = self._command_cell.build(
            CommandCellRequest(
                title=request.title,
                supported_event=request.event_type,
                command_focus=request.mission_or_training_goal,
                audience=request.audience,
                coordinating_sections=["XO", "Chief", "Battle Captain", *request.coordinating_sections[:4]],
                critical_decisions=_commander_decisions(request, s3_plan, s4_plan)[:4],
                due_outs=[
                    *xo_sync.due_out_tracker[:2],
                    *s3_plan.required_outputs[:2],
                    *s4_plan.coordination_points[:2],
                    *s6_plan.comm_plan_outline[:1],
                ],
                constraints=request.constraints,
                training_only=request.training_only,
            )
        )
        s1_readiness = self._s1.build(
            S1ReadinessRequest(
                title=request.title,
                supported_event=request.event_type,
                audience=request.audience,
                admin_priorities=[
                    "Roster and accountability visibility",
                    "Orders and routing ownership",
                    "Travel/admin suspense discipline",
                    *request.coordinating_sections[:2],
                ],
                admin_risks=[
                    "Late routing or stale rosters can quietly displace execution focus.",
                    "Travel/admin friction can consume the next planning cycle if left verbal.",
                    *request.constraints[:2],
                ],
                constraints=request.constraints,
                travel_required=_has_travel_indicator(request),
                training_only=request.training_only,
            )
        )
        safety_plan = self._safety.build(
            SafetyPlanningRequest(
                title=request.title,
                supported_event=request.event_type,
                audience=request.audience,
                hazards=request.medical_risk_context or _default_safety_hazards(request),
                controls=[
                    "Named stop-training authority",
                    "Medical response and accountability check",
                    "Communications/reporting fallback",
                ],
                risk_decisions=[
                    "What risk is acceptable versus event-canceling?",
                    "What control measure must be rehearsed before execution?",
                ],
                live_fire=_looks_like_live_fire(request),
                vehicle_ops=_looks_like_vehicle_ops(request),
                overnight=_has_overnight_indicator(request),
                constraints=request.constraints,
                training_only=request.training_only,
            )
        )
        sel_plan = self._sel.build(
            SelExecutionRequest(
                title=request.title,
                supported_event=request.event_type,
                audience=request.audience,
                accountability_risks=[
                    "Distributed Marines create handoff and accountability drift between drills.",
                    "Sequence control breaks when leaders assume everyone understands the same flow.",
                    *request.constraints[:2],
                ],
                constraints=request.constraints,
                formal_event=_looks_like_formal_event(request),
                overnight=_has_overnight_indicator(request),
                training_only=request.training_only,
            )
        )
        medical_plan = self._medical.build(
            MedicalPlanningRequest(
                title=request.title,
                supported_event=request.event_type,
                medical_risk_context=request.medical_risk_context or _default_medical_risks(request),
                casualty_scenarios=request.casualty_scenarios or _default_casualty_scenarios(request),
                audience=request.audience,
                overnight=_has_overnight_indicator(request),
                travel_required=_has_travel_indicator(request),
                training_only=request.training_only,
            )
        )

        g9_plan = None
        include_g9 = request.include_g9 if request.include_g9 is not None else _needs_g9(request)
        if include_g9:
            g9_plan = self._g9.build(
                G9PlanningRequest(
                    title=request.title,
                    supported_problem=request.mission_or_training_goal,
                    audience=request.audience,
                    partner_types=request.partner_types,
                    civil_considerations=request.civil_considerations,
                    constraints=request.constraints,
                    training_only=request.training_only,
                )
            )

        battalion_roles = ["s1", "s2", "s3", "s4", "s6", "surgeon"]
        battalion_review = self._council.vet_idea(
            StaffCouncilRequest(
                question=_planning_question(request),
                echelon=StaffEchelon.battalion,
                roles=battalion_roles,
                context={"source_items": request.source_items, "planning_focus": request.mission_or_training_goal},
            )
        )

        general_staff_review = None
        if include_g9:
            general_staff_review = self._council.vet_idea(
                StaffCouncilRequest(
                    question=_planning_question(request),
                    echelon=StaffEchelon.division_group,
                    roles=["g9"],
                    context={"source_items": request.source_items, "planning_focus": request.mission_or_training_goal},
                )
            )

        xo_vet = self._council.vet_idea(
            StaffCouncilRequest(
                question=_planning_question(request),
                echelon=StaffEchelon.battalion,
                roles=["xo"],
                context={"source_items": request.source_items, "planning_focus": request.mission_or_training_goal},
            )
        )

        product_package = [
            self._products.build(
                StaffProductDraftRequest(
                    product_type=product_type,
                    topic=request.title,
                    audience=request.audience,
                    echelon="battalion",
                    preferred_format=request.preferred_format,
                    facts=_product_facts(
                        request=request,
                        product_type=product_type,
                        planning_approach=planning_approach,
                        s2_estimate=s2_estimate,
                        s3_plan=s3_plan,
                        s4_plan=s4_plan,
                        s6_plan=s6_plan,
                        xo_sync=xo_sync,
                        command_cell=command_cell,
                        s1_readiness=s1_readiness,
                        safety_plan=safety_plan,
                        sel_plan=sel_plan,
                        medical_plan=medical_plan,
                        include_g9=include_g9,
                    ),
                    constraints=request.constraints,
                    training_or_fictional=request.training_only,
                )
            )
            for product_type in _resolved_product_types(request, s2_estimate)
        ]

        return StaffPlanningPackageResponse(
            title=f"Staff planning package: {request.title}",
            summary=_summary_lines(request, include_g9),
            planning_approach=planning_approach,
            recommended_course_of_action=_recommended_coa(request, s3_plan, s4_plan, s6_plan, include_g9),
            commander_decisions_now=_commander_decisions(request, s3_plan, s4_plan),
            top_risks=_top_risks(s3_plan, s4_plan, s6_plan, medical_plan),
            cuts_and_deferments=_cuts_and_deferments(request),
            execution_framework=_execution_framework(s3_plan, s4_plan, s6_plan, medical_plan),
            recommended_actions=_recommended_actions(s3_plan, battalion_review, xo_vet, include_g9),
            s2_estimate=s2_estimate,
            s3_plan=s3_plan,
            s4_plan=s4_plan,
            s6_plan=s6_plan,
            xo_sync=xo_sync,
            command_cell=command_cell,
            s1_readiness=s1_readiness,
            safety_plan=safety_plan,
            sel_plan=sel_plan,
            medical_plan=medical_plan,
            g9_plan=g9_plan,
            battalion_staff_review=battalion_review,
            general_staff_review=general_staff_review,
            xo_vet=xo_vet,
            product_package=product_package,
            warnings=[
                *DEFAULT_WARNINGS,
                *boundary_warnings,
                "This package is advisory only and should be reviewed by the appropriate command and staff chain.",
            ],
        )

    def _build_s2_estimate(self, request: StaffPlanningPackageRequest) -> S2EstimateResponse | None:
        if not request.source_items and not request.intelligence_question:
            return None
        return self._s2.build(
            S2EstimateRequest(
                title=request.title,
                question=request.intelligence_question
                or f"What public-source context most affects {request.mission_or_training_goal}?",
                source_items=request.source_items,
                audience=request.audience,
                timeframe=request.timeframe,
                planning_only=request.training_only,
            )
        )


def _resolved_product_types(
    request: StaffPlanningPackageRequest, s2_estimate: S2EstimateResponse | None
) -> list[StaffProductType]:
    product_types = list(request.product_types)
    product_types.append(StaffProductType.running_estimate)

    if _needs_synchronization_matrix(request):
        product_types.append(StaffProductType.synchronization_matrix)
        product_types.append(StaffProductType.decision_support_matrix)
        product_types.append(StaffProductType.due_out_tracker)
    if _needs_safety_products(request):
        product_types.append(StaffProductType.orm_worksheet)
        product_types.append(StaffProductType.no_go_criteria)
        product_types.append(StaffProductType.residual_risk_decision_note)
        product_types.append(StaffProductType.rehearsal_safety_brief)
    if _needs_admin_products(request):
        product_types.append(StaffProductType.admin_estimate)
        product_types.append(StaffProductType.admin_task_tracker)
        product_types.append(StaffProductType.routing_matrix)
        product_types.append(StaffProductType.pre_drill_admin_readiness_check)
    if _needs_sel_products(request):
        product_types.append(StaffProductType.troop_flow_checklist)
        product_types.append(StaffProductType.formation_transition_matrix)
        product_types.append(StaffProductType.leader_touchpoint_plan)
    if s2_estimate is not None:
        product_types.append(StaffProductType.road_to_war_brief)
        product_types.append(StaffProductType.collection_matrix)
    elif _needs_road_to_war_brief(request):
        product_types.append(StaffProductType.road_to_war_brief)
    if _needs_sustainment_matrix(request):
        product_types.append(StaffProductType.sustainment_matrix)
        product_types.append(StaffProductType.movement_table)
    if _needs_medical_estimate(request):
        product_types.append(StaffProductType.medical_estimate)
        product_types.append(StaffProductType.casevac_quick_card)

    return list(dict.fromkeys(product_types))


def _planning_question(request: StaffPlanningPackageRequest) -> str:
    return (
        f"Build a feasible staff-backed plan for {request.title}. "
        f"Goal: {request.mission_or_training_goal}. Event type: {request.event_type}."
    )


def _has_travel_indicator(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join(
        [request.event_type, request.timeframe or "", *request.constraints, *request.support_requirements]
    ).lower()
    return any(term in text for term in {"travel", "movement", "distributed", "overnight", "miami", "at "})


def _has_overnight_indicator(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join([request.event_type, request.timeframe or "", *request.constraints]).lower()
    return any(term in text for term in {"overnight", "multi-day", "field day plus", "at "})


def _needs_g9(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join(
        [
            request.title,
            request.mission_or_training_goal,
            *request.partner_types,
            *request.civil_considerations,
            *request.constraints,
        ]
    ).lower()
    return any(
        term in text
        for term in {
            "civil",
            "community",
            "partner",
            "ngo",
            "interagency",
            "humanitarian",
            "disaster",
            "population",
            "local authority",
            "civil affairs",
        }
    )


def _needs_synchronization_matrix(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.coordinating_sections
        or request.support_requirements
        or _has_travel_indicator(request)
        or _has_overnight_indicator(request)
    )


def _needs_sustainment_matrix(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.support_requirements
        or _has_travel_indicator(request)
        or _has_overnight_indicator(request)
        or _looks_like_vehicle_ops(request)
    )


def _needs_admin_products(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.coordinating_sections
        or _has_travel_indicator(request)
        or request.event_type
        or request.audience
    )


def _needs_safety_products(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.medical_risk_context
        or _looks_like_live_fire(request)
        or _looks_like_vehicle_ops(request)
        or _has_overnight_indicator(request)
        or _has_travel_indicator(request)
        or request.support_requirements
        or request.coordinating_sections
    )


def _needs_sel_products(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.event_type
        or request.audience
        or request.coordinating_sections
        or _has_travel_indicator(request)
        or _has_overnight_indicator(request)
        or _looks_like_formal_event(request)
    )


def _needs_medical_estimate(request: StaffPlanningPackageRequest) -> bool:
    return bool(
        request.medical_risk_context
        or request.casualty_scenarios
        or _looks_like_live_fire(request)
        or _looks_like_vehicle_ops(request)
        or _has_overnight_indicator(request)
        or _has_travel_indicator(request)
    )


def _needs_road_to_war_brief(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join(
        [
            request.title,
            request.event_type,
            request.mission_or_training_goal,
            request.audience or "",
            request.timeframe or "",
            request.intelligence_question or "",
            *request.partner_types,
            *request.civil_considerations,
            *request.constraints,
            *request.support_requirements,
        ]
    ).lower()
    return bool(
        request.source_items
        or request.intelligence_question
        or request.partner_types
        or request.civil_considerations
        or any(
            term in text
            for term in {
                "scenario",
                "region",
                "regional",
                "theater",
                "crisis",
                "contingency",
                "littoral",
                "country",
                "adversary",
                "threat",
                "road to war",
            }
        )
    )


def _default_medical_risks(request: StaffPlanningPackageRequest) -> list[str]:
    return [
        "Heat, dehydration, fatigue, and field-injury assumptions must be validated.",
        f"Event context: {request.event_type}",
    ]


def _default_safety_hazards(request: StaffPlanningPackageRequest) -> list[str]:
    return [
        "Loss of positive control or accountability under compressed timelines.",
        "Medical or communications support assumptions breaking under friction.",
        f"Event context hazard: {request.event_type}",
    ]


def _default_casualty_scenarios(request: StaffPlanningPackageRequest) -> list[str]:
    return ["Heat casualty", "Vehicle mishap", "Training injury during movement or field activity"]


def _looks_like_live_fire(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join([request.title, request.event_type, request.mission_or_training_goal, *request.constraints]).lower()
    return any(term in text for term in {"live fire", "range", "weapons", "ammo", "sdz"})


def _looks_like_vehicle_ops(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join([request.title, request.event_type, *request.constraints, *request.support_requirements]).lower()
    return any(term in text for term in {"vehicle", "convoy", "movement", "bus", "driver"})


def _looks_like_formal_event(request: StaffPlanningPackageRequest) -> bool:
    text = " ".join([request.title, request.event_type, request.mission_or_training_goal]).lower()
    return any(
        term in text
        for term in {"ceremony", "change of command", "formal", "parade", "honors", "memorial", "public-facing"}
    )


def _summary_lines(request: StaffPlanningPackageRequest, include_g9: bool) -> list[str]:
    lines = [
        f"Primary effort: {request.mission_or_training_goal}",
        "Build the smallest plan that still trains to a real standard and can actually be resourced.",
        "Separate decision points from admin noise early or the drill weekend will disappear into churn.",
    ]
    if include_g9:
        lines.append("Civil-military considerations are relevant enough to include a G-9 review.")
    return lines


def _recommended_coa(
    request: StaffPlanningPackageRequest,
    s3_plan: S3PlanningResponse,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    include_g9: bool,
) -> list[str]:
    planning_approach = assess_planning_approach(
        title=request.title,
        mission_or_training_goal=request.mission_or_training_goal,
        event_type=request.event_type,
        timeframe=request.timeframe,
        constraints=request.constraints,
        higher_guidance=[],
        coordinating_sections=request.coordinating_sections,
        support_requirements=request.support_requirements,
        partner_types=request.partner_types,
        civil_considerations=request.civil_considerations,
        subordinate_unit_count=0,
        source_items_present=False,
    )
    coa = [
        "Approve one main effort, one supporting effort, and cut anything that dilutes them.",
        "Lock the critical-path products before drill ends: task list, short schedule, support asks, "
        "and AAR structure.",
        "Keep the execution concept simple enough to brief quickly, rehearse once, and assess honestly.",
        "Use S-4 and S-6 early so support and information flow shape the plan before the plan hardens.",
        "Treat unresolved assumptions as named risks with owners, not as optimistic background noise.",
        f"Planning method: {planning_approach.recommended_method.upper()} - {planning_approach.decision}",
    ]
    if include_g9:
        coa.append(
            "Fold civil or partner coordination into the plan deliberately instead of treating it "
            "as an afterthought."
        )
    if s3_plan.required_outputs:
        coa.append(f"Required output to protect first: {s3_plan.required_outputs[0]}")
    if s4_plan.critical_support_requirements:
        coa.append(f"Support reality check: {s4_plan.critical_support_requirements[0]}")
    if s6_plan.pace_considerations:
        coa.append(f"C2 reality check: {s6_plan.pace_considerations[0]}")
    return coa


def _commander_decisions(
    request: StaffPlanningPackageRequest, s3_plan: S3PlanningResponse, s4_plan: S4PlanningResponse
) -> list[str]:
    return [
        "Approve the primary training objective and what will be cut to protect it.",
        "Approve the event scope the unit can actually resource inside the reserve timeline.",
        "Decide which support shortfall is acceptable and which one cancels or modifies the event.",
        "Decide what must be complete by close of drill and what can survive as follow-on action.",
        *s3_plan.command_decision_points[:2],
        *s4_plan.coordination_points[:1],
    ]


def _top_risks(
    s3_plan: S3PlanningResponse,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    medical_plan: MedicalPlanningResponse,
) -> list[str]:
    return [
        f"Training architecture risk: {s3_plan.reserve_friction_points[0]}",
        f"Supportability risk: {s4_plan.reserve_friction_points[0]}",
        f"C2 risk: {s6_plan.reserve_friction_points[0]}",
        f"Medical/CASEVAC risk: {medical_plan.coordination_requirements[0]}",
    ]


def _cuts_and_deferments(request: StaffPlanningPackageRequest) -> list[str]:
    return [
        "Cut anything that is not tied to a real training standard, required output, or command decision.",
        "Defer nice-to-have extras that add complexity without adding assessment value.",
        "Push non-critical admin follow-ups into tracked actions instead of letting them dominate execution time.",
        "If a lane, support ask, or inject cannot be resourced and rehearsed, cut it now instead of excusing it later.",
        *[f"Constraint-driven cut candidate: {item}" for item in request.constraints[:2]],
    ]


def _execution_framework(
    s3_plan: S3PlanningResponse,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    medical_plan: MedicalPlanningResponse,
) -> list[str]:
    return [
        "Design the event around one clear main effort and one simple reporting rhythm.",
        *s3_plan.battle_rhythm[:3],
        *s4_plan.movement_and_billeting[:1],
        *s6_plan.pace_considerations[:1],
        *medical_plan.casevac_plan_elements[:1],
    ]


def _recommended_actions(
    s3_plan: S3PlanningResponse,
    battalion_review: StaffCouncilResponse,
    xo_vet: StaffCouncilResponse,
    include_g9: bool,
) -> list[str]:
    actions = [
        "Publish the short planning focus, desired end state, and critical-path suspense list.",
        "Assign owners to every required product before the close of drill.",
        "Track unresolved support, comm, and medical assumptions as named actions instead of leaving them verbal.",
        "Write down what gets cut, who approved the cut, and what condition would justify bringing it back.",
        *s3_plan.required_outputs[:2],
    ]
    if battalion_review.perspectives:
        actions.append(f"Staff friction to resolve first: {battalion_review.perspectives[0].role}")
    if xo_vet.perspectives:
        actions.append("XO review standard: owner, suspense, command decision, and failure point must be explicit.")
    if include_g9:
        actions.append("Capture external coordination and continuity notes in a turnover format before dismissal.")
    return actions


def _product_facts(
    request: StaffPlanningPackageRequest,
    product_type: StaffProductType,
    planning_approach: PlanningApproachAssessment,
    s2_estimate: S2EstimateResponse | None,
    s3_plan: S3PlanningResponse,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    xo_sync: XoSyncResponse,
    command_cell: CommandCellResponse,
    s1_readiness: S1ReadinessResponse,
    safety_plan: SafetyPlanningResponse,
    sel_plan: SelExecutionResponse,
    medical_plan: MedicalPlanningResponse,
    include_g9: bool,
) -> list[str]:
    facts = [
        f"Training goal: {request.mission_or_training_goal}",
        f"Event type: {request.event_type}",
        f"Recommended planning method: {planning_approach.recommended_method.upper()}",
        f"Planning decision: {planning_approach.decision}",
        *[f"Support requirement: {item}" for item in request.support_requirements[:3]],
    ]

    if product_type == StaffProductType.running_estimate:
        facts.extend(
            [
                f"Primary staff friction: {s3_plan.reserve_friction_points[0]}",
                f"Supportability friction: {s4_plan.reserve_friction_points[0]}",
                f"C2 friction: {s6_plan.reserve_friction_points[0]}",
                f"Admin focus: {s1_readiness.readiness_estimate[0]}",
            ]
        )
    elif product_type == StaffProductType.synchronization_matrix:
        facts.extend(
            [
                f"Battle rhythm checkpoint: {s3_plan.battle_rhythm[0]}",
                f"Coordination point: {s4_plan.coordination_points[0]}",
                f"Command synchronization focus: {xo_sync.command_sync_frame[0]}",
                f"Leader touchpoint: {sel_plan.leader_touchpoints[0]}",
            ]
        )
    elif product_type == StaffProductType.orm_worksheet:
        facts.extend(
            [
                f"ORM frame: {safety_plan.orm_framework[0]}",
                f"Named hazard or control: {safety_plan.orm_framework[-1]}",
                f"Residual-risk focus: {safety_plan.residual_risk_decisions[0]}",
                f"Rehearsal check: {safety_plan.rehearsal_checks[0]}",
            ]
        )
    elif product_type == StaffProductType.no_go_criteria:
        facts.extend(
            [
                f"No-go baseline: {safety_plan.no_go_criteria[0]}",
                f"Event-specific stop condition: {safety_plan.no_go_criteria[-1]}",
                f"Stop-training trigger: {safety_plan.stop_training_triggers[0]}",
                f"Command review point: {xo_sync.command_review_points[2]}",
            ]
        )
    elif product_type == StaffProductType.residual_risk_decision_note:
        facts.extend(
            [
                f"Residual-risk decision focus: {safety_plan.residual_risk_decisions[0]}",
                f"Named risk decision: {safety_plan.residual_risk_decisions[-1]}",
                f"Commander decision support: {xo_sync.decision_support_matrix[0]}",
                f"No-go threshold: {safety_plan.no_go_criteria[0]}",
            ]
        )
    elif product_type == StaffProductType.rehearsal_safety_brief:
        facts.extend(
            [
                f"Rehearsal safety focus: {safety_plan.rehearsal_checks[0]}",
                f"Stop-training authority trigger: {safety_plan.stop_training_triggers[0]}",
                f"ORM frame: {safety_plan.orm_framework[1]}",
                f"Command-cell brief line: {command_cell.command_update_lines[0]}",
            ]
        )
    elif product_type == StaffProductType.admin_estimate:
        facts.extend(
            [
                f"Admin estimate focus: {s1_readiness.readiness_estimate[0]}",
                f"Admin status board item: {s1_readiness.admin_status_board[0]}",
                f"Critical suspense: {s1_readiness.critical_suspenses[0]}",
                f"Continuity note: {s1_readiness.continuity_notes[0]}",
            ]
        )
    elif product_type == StaffProductType.admin_task_tracker:
        facts.extend(
            [
                f"Admin task tracker focus: {s1_readiness.admin_task_tracker[0]}",
                f"Admin status board item: {s1_readiness.admin_status_board[1]}",
                f"Chief focus support: {command_cell.chief_focus_board[0]}",
                f"Turnover note: {command_cell.turnover_handoff_notes[0]}",
            ]
        )
    elif product_type == StaffProductType.routing_matrix:
        facts.extend(
            [
                f"Routing matrix focus: {s1_readiness.routing_matrix[0]}",
                f"Routing dependency: {s1_readiness.routing_matrix[-1]}",
                f"Command touchpoint: {xo_sync.due_out_tracker[0]}",
                f"Constraint to manage: {s1_readiness.critical_suspenses[-1]}",
            ]
        )
    elif product_type == StaffProductType.pre_drill_admin_readiness_check:
        facts.extend(
            [
                f"Pre-drill check focus: {s1_readiness.pre_drill_admin_readiness_check[0]}",
                f"Roster or accountability check: {s1_readiness.admin_status_board[0]}",
                f"Travel-admin check: {s1_readiness.pre_drill_admin_readiness_check[-1]}",
                f"Immediate suspense: {s1_readiness.critical_suspenses[0]}",
            ]
        )
    elif product_type == StaffProductType.troop_flow_checklist:
        facts.extend(
            [
                f"Troop-flow focus: {sel_plan.troop_flow_plan[0]}",
                f"Troop-flow checklist item: {sel_plan.troop_flow_checklist[0]}",
                f"Accountability scheme: {sel_plan.accountability_scheme[0]}",
                f"Leader touchpoint: {sel_plan.leader_touchpoint_plan[0]}",
            ]
        )
    elif product_type == StaffProductType.formation_transition_matrix:
        facts.extend(
            [
                f"Formation/transition focus: {sel_plan.formation_transition_matrix[0]}",
                f"Transition control item: {sel_plan.formation_transition_matrix[1]}",
                f"Standards check: {sel_plan.standards_checks[0]}",
                f"Marine-impact check: {sel_plan.marine_welfare_checks[0]}",
            ]
        )
    elif product_type == StaffProductType.leader_touchpoint_plan:
        facts.extend(
            [
                f"Leader touchpoint focus: {sel_plan.leader_touchpoint_plan[0]}",
                f"Phase-change touchpoint: {sel_plan.leader_touchpoint_plan[1]}",
                f"Welfare check: {sel_plan.marine_welfare_checks[0]}",
                f"Accountability owner note: {sel_plan.accountability_scheme[1]}",
            ]
        )
    elif product_type == StaffProductType.decision_support_matrix:
        facts.extend(
            [
                f"Command decision support: {xo_sync.decision_support_matrix[0]}",
                f"Command update line: {command_cell.command_update_lines[0]}",
                f"CCIR or escalation trigger: {command_cell.ccir_and_decision_triggers[0]}",
                f"Support reality check: {s4_plan.coordination_points[0]}",
            ]
        )
    elif product_type == StaffProductType.due_out_tracker:
        facts.extend(
            [
                f"Due-out tracker focus: {xo_sync.due_out_tracker[0]}",
                f"Chief focus board item: {command_cell.chief_focus_board[0]}",
                f"Battle captain watchboard item: {command_cell.battle_captain_watchboard[0]}",
                f"Turnover note: {command_cell.turnover_handoff_notes[0]}",
            ]
        )
    elif product_type == StaffProductType.collection_matrix and s2_estimate is not None:
        facts.extend(
            [
                f"Intelligence summary: {s2_estimate.summary_assessment[0]}",
                f"Assessment focus: {s2_estimate.assessed_claims[0]}",
                f"Collection gap: {s2_estimate.collection_gaps[0]}",
                f"Decision support: {s2_estimate.command_considerations[0]}",
            ]
        )
    elif product_type == StaffProductType.road_to_war_brief:
        partner_or_civil = (
            request.partner_types[0]
            if request.partner_types
            else request.civil_considerations[0] if request.civil_considerations else "None stated"
        )
        first_unit_concern = (
            s2_estimate.command_considerations[0] if s2_estimate is not None else planning_approach.decision
        )
        facts.extend(
            [
                (
                    f"Scenario framing question: "
                    f"{request.intelligence_question or f'What unit-entry context matters most for {request.title}?'}"
                ),
                (
                    f"Public-source context available: "
                    f"{'yes' if request.source_items else 'no, build from stated scenario cues and verify before use'}"
                ),
                (
                    f"Partner or civil frame: "
                    f"{partner_or_civil}"
                ),
                (f"First-unit concern: " f"{first_unit_concern}"),
            ]
        )
    elif product_type == StaffProductType.sustainment_matrix:
        facts.extend(
            [
                f"Critical support requirement: {s4_plan.critical_support_requirements[0]}",
                f"Movement or billeting note: {s4_plan.movement_and_billeting[0]}",
                f"Report and comm dependency: {s6_plan.comm_plan_outline[0]}",
                f"Safety control: {safety_plan.orm_framework[0]}",
            ]
        )
    elif product_type == StaffProductType.movement_table:
        facts.extend(
            [
                f"Movement-table focus: {s4_plan.movement_and_billeting[0]}",
                f"Critical support requirement: {s4_plan.critical_support_requirements[0]}",
                f"Coordination point: {s4_plan.coordination_points[0]}",
                f"Accountability touchpoint: {sel_plan.accountability_scheme[0]}",
            ]
        )
    elif product_type == StaffProductType.medical_estimate:
        facts.extend(
            [
                f"Medical estimate focus: {medical_plan.medical_support_estimate[0]}",
                f"TCCC knowledge point: {medical_plan.tccc_knowledge_points[0]}",
                f"CASEVAC planning element: {medical_plan.casevac_plan_elements[0]}",
                f"CASEVAC/MEDEVAC check: {medical_plan.casevac_medevac_check[0]}",
                f"Casualty collection logic: {medical_plan.casualty_collection_logic[0]}",
                f"Medical decision point: {medical_plan.medical_decision_points[0]}",
                f"Medical coordination requirement: {medical_plan.coordination_requirements[0]}",
                f"Medical coordination trigger: {medical_plan.coordination_trigger_list[0]}",
            ]
        )
    elif product_type == StaffProductType.casevac_quick_card:
        facts.extend(
            [
                f"CASEVAC quick-card focus: {medical_plan.casevac_plan_elements[0]}",
                f"CASEVAC/MEDEVAC check: {medical_plan.casevac_medevac_check[0]}",
                f"Casualty collection logic: {medical_plan.casualty_collection_logic[0]}",
                f"Stop-training or decision trigger: {medical_plan.medical_decision_points[0]}",
            ]
        )

    if include_g9:
        facts.append("Civil or partner coordination is relevant enough to remain visible in staff integration.")
    return facts


def _request_text(request: StaffPlanningPackageRequest) -> str:
    return " ".join(
        [
            request.title,
            request.event_type,
            request.mission_or_training_goal,
            request.audience or "",
            request.timeframe or "",
            request.intelligence_question or "",
            request.c2_objective or "",
            request.support_objective or "",
            *request.constraints,
            *request.coordinating_sections,
            *request.support_requirements,
            *request.partner_types,
            *request.civil_considerations,
            *request.medical_risk_context,
            *request.casualty_scenarios,
            *[str(item) for item in request.source_items],
        ]
    )


def _sanitize_staff_package_request(request: StaffPlanningPackageRequest) -> StaffPlanningPackageRequest:
    return request.model_copy(
        update={
            "title": "Sensitive planning request withheld",
            "mission_or_training_goal": (
                "Provide only a generic training-only planning checklist and route specific details through approved "
                "channels."
            ),
            "audience": None,
            "timeframe": None,
            "constraints": ["Sensitive operational details were withheld."],
            "coordinating_sections": [],
            "support_requirements": [],
            "partner_types": [],
            "civil_considerations": [],
            "medical_risk_context": ["Use generic training-safe medical planning only."],
            "casualty_scenarios": ["Generic training injury scenario only."],
            "source_items": [],
            "intelligence_question": None,
            "c2_objective": None,
            "support_objective": None,
            "include_g9": False,
            "training_only": True,
        }
    )
