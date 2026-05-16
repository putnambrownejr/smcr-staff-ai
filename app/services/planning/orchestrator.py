from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.planning import StaffPlanningPackageRequest, StaffPlanningPackageResponse
from app.schemas.staff import (
    G9PlanningRequest,
    MedicalPlanningRequest,
    MedicalPlanningResponse,
    S2EstimateRequest,
    S2EstimateResponse,
    S6PlanRequest,
    S6PlanResponse,
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffEchelon,
)
from app.schemas.staff_products import StaffProductDraftRequest
from app.schemas.training import S3PlanningRequest, S3PlanningResponse, S4PlanningRequest, S4PlanningResponse
from app.services.staff.council import StaffCouncilService
from app.services.staff.g9_planner import G9Planner
from app.services.staff.medical_planner import MedicalPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff_products.builder import StaffProductBuilder
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner


class StaffPlanningOrchestrator:
    def __init__(self) -> None:
        self._s2 = S2Estimator()
        self._s3 = S3Planner()
        self._s4 = S4Planner()
        self._s6 = S6Planner()
        self._medical = MedicalPlanner()
        self._g9 = G9Planner()
        self._council = StaffCouncilService()
        self._products = StaffProductBuilder()

    def build(self, request: StaffPlanningPackageRequest) -> StaffPlanningPackageResponse:
        boundary_warnings = detect_sensitive_input(_request_text(request))
        if boundary_warnings:
            request = _sanitize_staff_package_request(request)
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
                    facts=[
                        f"Training goal: {request.mission_or_training_goal}",
                        f"Event type: {request.event_type}",
                        *[f"Support requirement: {item}" for item in request.support_requirements[:3]],
                    ],
                    constraints=request.constraints,
                    training_or_fictional=request.training_only,
                )
            )
            for product_type in request.product_types
        ]

        return StaffPlanningPackageResponse(
            title=f"Staff planning package: {request.title}",
            summary=_summary_lines(request, include_g9),
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


def _default_medical_risks(request: StaffPlanningPackageRequest) -> list[str]:
    return [
        "Heat, dehydration, fatigue, and field-injury assumptions must be validated.",
        f"Event context: {request.event_type}",
    ]


def _default_casualty_scenarios(request: StaffPlanningPackageRequest) -> list[str]:
    return ["Heat casualty", "Vehicle mishap", "Training injury during movement or field activity"]


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
    coa = [
        "Approve one main effort, one supporting effort, and cut anything that dilutes them.",
        "Lock the critical-path products before drill ends: task list, short schedule, support asks, "
        "and AAR structure.",
        "Keep the execution concept simple enough to brief quickly, rehearse once, and assess honestly.",
        "Use S-4 and S-6 early so support and information flow shape the plan before the plan hardens.",
        "Treat unresolved assumptions as named risks with owners, not as optimistic background noise.",
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
