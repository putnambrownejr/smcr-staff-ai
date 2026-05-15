from app.core.security import DEFAULT_WARNINGS
from app.schemas.planning import (
    FragoToConopRequest,
    FragoToConopResponse,
    MetAlignmentItem,
    UnitRelationshipFrame,
)
from app.schemas.staff import (
    G9PlanningRequest,
    MedicalPlanningRequest,
    MedicalPlanningResponse,
    S2EstimateRequest,
    S2EstimateResponse,
    S6PlanRequest,
    S6PlanResponse,
)
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.schemas.training import S3PlanningRequest, S3PlanningResponse, S4PlanningRequest, S4PlanningResponse
from app.services.staff.g9_planner import G9Planner
from app.services.staff.medical_planner import MedicalPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff_products.builder import StaffProductBuilder
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner


class FragoToConopBuilder:
    def __init__(self) -> None:
        self._s2 = S2Estimator()
        self._s3 = S3Planner()
        self._s4 = S4Planner()
        self._s6 = S6Planner()
        self._medical = MedicalPlanner()
        self._g9 = G9Planner()
        self._products = StaffProductBuilder()

    def build(self, request: FragoToConopRequest) -> FragoToConopResponse:
        s2_estimate = self._build_s2_estimate(request)
        s3_plan = self._s3.build(
            S3PlanningRequest(
                title=request.title,
                mission_or_training_goal=request.mission_or_training_goal,
                event_type=request.event_type,
                audience=request.supported_unit,
                timeframe=request.timeframe,
                constraints=[*request.constraints, *request.higher_guidance[:2]],
                coordinating_sections=request.coordinating_sections or ["S-1", "S-4", "S-6", "Medical"],
                training_only=request.training_only,
            )
        )
        s4_plan = self._s4.build(
            S4PlanningRequest(
                title=request.title,
                supported_event=request.event_type,
                support_objective=(
                    "Support subordinate-unit execution and sustainment "
                    "without overloading the company timeline."
                ),
                audience=request.supported_unit,
                travel_required=_has_travel_indicator(request),
                overnight=_has_overnight_indicator(request),
                distributed_personnel=len(request.subordinate_units) > 1,
                constraints=request.constraints,
                support_requirements=request.support_requirements,
            )
        )
        s6_plan = self._s6.build(
            S6PlanRequest(
                title=request.title,
                supported_event=request.event_type,
                c2_objective="Support reporting, accountability, and company-to-subordinate information flow.",
                audience=request.supported_unit,
                distributed_personnel=len(request.subordinate_units) > 1,
                constraints=request.constraints,
                support_requirements=request.support_requirements,
                training_only=request.training_only,
            )
        )
        medical_plan = self._medical.build(
            MedicalPlanningRequest(
                title=request.title,
                supported_event=request.event_type,
                medical_risk_context=request.medical_risk_context
                or ["Heat, fatigue, and field-injury assumptions require validation."],
                casualty_scenarios=request.casualty_scenarios
                or ["Training injury", "Heat casualty during movement"],
                audience=request.supported_unit,
                overnight=_has_overnight_indicator(request),
                travel_required=_has_travel_indicator(request),
                training_only=request.training_only,
            )
        )
        include_g9 = _needs_g9(request)
        g9_plan = None
        if include_g9:
            g9_plan = self._g9.build(
                G9PlanningRequest(
                    title=request.title,
                    supported_problem=request.mission_or_training_goal,
                    audience=request.supported_unit,
                    partner_types=request.partner_types,
                    civil_considerations=[*request.civil_considerations, *request.g9_inputs],
                    constraints=request.constraints,
                    training_only=request.training_only,
                )
            )

        relationship_framework = _unit_relationship_framework(request, s4_plan, s6_plan)
        met_alignment = _met_alignment(request)

        frago_facts = [
            f"Higher headquarters: {request.higher_headquarters}" if request.higher_headquarters else None,
            f"Supported unit: {request.supported_unit}",
            f"Mission/training goal: {request.mission_or_training_goal}",
            *[f"Higher guidance: {item}" for item in request.higher_guidance[:4]],
            *[f"S-3 input: {item}" for item in request.s3_inputs[:3]],
            *[f"G-9 input: {item}" for item in request.g9_inputs[:3]],
        ]
        frago_draft = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.frago,
                topic=request.title,
                audience=request.supported_unit,
                echelon="company",
                preferred_format=request.preferred_format,
                facts=[item for item in frago_facts if item],
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )

        conop_facts = [
            f"Supported unit: {request.supported_unit}",
            *[
                f"Subordinate relationship: {frame.unit_name} / {frame.relationship}"
                for frame in relationship_framework
            ],
            *[f"MET/METL alignment: {item.task_name} ({item.alignment_type})" for item in met_alignment[:4]],
            *[f"Support dependency: {item}" for item in s4_plan.critical_support_requirements[:3]],
        ]
        initial_conop = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.conop,
                topic=f"Initial CONOP for {request.title}",
                audience=request.supported_unit,
                echelon="company",
                preferred_format=request.preferred_format,
                facts=conop_facts,
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )

        aar_facts = [
            f"Supported unit: {request.supported_unit}",
            *[f"Assess against: {item.task_name}" for item in met_alignment[:4]],
            "Capture observations by unit/sub-unit, standard, friction point, and corrective action.",
        ]
        aar_framework = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.aar,
                topic=f"AAR framework for {request.title}",
                audience=request.supported_unit,
                echelon="company",
                facts=aar_facts,
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )

        return FragoToConopResponse(
            title=f"FRAGO to CONOP package: {request.title}",
            guidance_summary=_guidance_summary(request),
            commander_focus=_commander_focus(request, s3_plan),
            unit_relationship_framework=relationship_framework,
            met_alignment=met_alignment,
            initial_conop=initial_conop,
            frago_draft=frago_draft,
            aar_framework=aar_framework,
            s2_estimate=s2_estimate,
            s3_plan=s3_plan,
            s4_plan=s4_plan,
            s6_plan=s6_plan,
            medical_plan=medical_plan,
            g9_plan=g9_plan,
            key_assumptions=_key_assumptions(request, s4_plan, s6_plan, medical_plan),
            key_risks=_key_risks(s3_plan, s4_plan, s6_plan, medical_plan),
            det_follow_on_questions=_follow_on_questions(request, relationship_framework),
            warnings=[
                *DEFAULT_WARNINGS,
                "This FRAGO-to-CONOP package is advisory and must be reviewed by the command and staff chain.",
            ],
        )

    def _build_s2_estimate(self, request: FragoToConopRequest) -> S2EstimateResponse | None:
        if not request.source_items and not request.intelligence_question:
            return None
        return self._s2.build(
            S2EstimateRequest(
                title=request.title,
                question=request.intelligence_question
                or f"What current public-source context most affects {request.mission_or_training_goal}?",
                source_items=request.source_items,
                audience=request.supported_unit,
                timeframe=request.timeframe,
                planning_only=request.training_only,
            )
        )


def _unit_relationship_framework(
    request: FragoToConopRequest,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
) -> list[UnitRelationshipFrame]:
    if not request.subordinate_units:
        return [
            UnitRelationshipFrame(
                unit_name=request.supported_unit,
                relationship="supported unit",
                task_focus=[
                    "Translate higher guidance into a workable company concept.",
                    "Issue clear subordinate tasks, support expectations, and reporting requirements.",
                ],
                support_dependencies=[
                    *s4_plan.critical_support_requirements[:2],
                    *s6_plan.support_requirements[:1],
                ],
                required_outputs=["Initial CONOP", "Refined FRAGO input", "AAR collection plan"],
            )
        ]

    return [
        UnitRelationshipFrame(
            unit_name=subordinate.unit_name,
            relationship=subordinate.relationship,
            task_focus=[
                subordinate.purpose or "Build a subordinate concept that supports the parent scheme.",
                *subordinate.planning_requirements[:2],
            ],
            support_dependencies=[
                *s4_plan.critical_support_requirements[:2],
                *s6_plan.support_requirements[:1],
            ],
            required_outputs=[
                "Subordinate concept sketch",
                "Support shortfall list",
                "AAR input by task and friction point",
            ],
        )
        for subordinate in request.subordinate_units
    ]


def _met_alignment(request: FragoToConopRequest) -> list[MetAlignmentItem]:
    items: list[MetAlignmentItem] = []
    for task in request.met_tasks:
        items.append(
            MetAlignmentItem(
                task_name=task,
                alignment_type="MET",
                why_it_matters=(
                    "This named task should drive the event design "
                    "instead of letting activity stand in for standards."
                ),
                assessment_focus=(
                    "What right looked like, what was observed, "
                    "and what must improve before the next iteration."
                ),
            )
        )
    for task in request.metl_focus:
        items.append(
            MetAlignmentItem(
                task_name=task,
                alignment_type="METL",
                why_it_matters=(
                    "This METL focus should anchor subordinate-unit purpose "
                    "and the commander's priority of effort."
                ),
                assessment_focus=(
                    "Measure whether subordinate units supported the larger training aim "
                    "rather than only completing their own lane."
                ),
            )
        )
    if not items:
        items.append(
            MetAlignmentItem(
                task_name="Training objective requires manual MET/METL mapping",
                alignment_type="manual_review",
                why_it_matters="The package should not pretend task alignment exists if the standard was never named.",
                assessment_focus="Identify the correct task standard before treating the plan as final.",
            )
        )
    return items


def _guidance_summary(request: FragoToConopRequest) -> list[str]:
    summary = [
        f"Supported unit: {request.supported_unit}",
        f"Event type: {request.event_type}",
        f"Planning focus: {request.mission_or_training_goal}",
        "Digest higher guidance into explicit tasks, relationships, and decision points "
        "before building subordinate concepts.",
    ]
    if request.higher_headquarters:
        summary.append(f"Higher headquarters guidance source: {request.higher_headquarters}")
    summary.extend(f"Higher-guidance note: {item}" for item in request.higher_guidance[:3])
    return summary


def _commander_focus(
    request: FragoToConopRequest, s3_plan: S3PlanningResponse
) -> list[str]:
    return [
        "Approve the supported unit's main effort and what subordinate effort is supporting versus decisive.",
        "Approve the scope that can actually be resourced and rehearsed inside the available timeline.",
        "Decide what must be directed in the FRAGO versus what subordinate units may refine in their own concepts.",
        *s3_plan.command_decision_points[:2],
    ]


def _key_assumptions(
    request: FragoToConopRequest,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    medical_plan: MedicalPlanningResponse,
) -> list[str]:
    assumptions = [
        "Higher guidance is stable enough to build an initial subordinate concept.",
        "Subordinate units will receive enough clarity to refine their own concepts "
        "instead of guessing command intent.",
        *s4_plan.sustainment_checks[:1],
        *s6_plan.permissions_and_dependencies[:1],
        *medical_plan.coordination_requirements[:1],
    ]
    assumptions.extend(f"Constraint-derived assumption: {item}" for item in request.constraints[:2])
    return assumptions


def _key_risks(
    s3_plan: S3PlanningResponse,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    medical_plan: MedicalPlanningResponse,
) -> list[str]:
    return [
        *s3_plan.reserve_friction_points[:1],
        *s4_plan.reserve_friction_points[:1],
        *s6_plan.reserve_friction_points[:1],
        *medical_plan.coordination_requirements[:1],
    ]


def _follow_on_questions(
    request: FragoToConopRequest,
    relationship_framework: list[UnitRelationshipFrame],
) -> list[str]:
    questions = [
        "What part of the parent's concept must remain fixed across all subordinate units?",
        "What support shortfall or command relationship still needs clarification "
        "before subordinate concepts can stabilize?",
        "What will the AAR need to compare across units or sub-units?",
    ]
    for frame in relationship_framework[:3]:
        questions.append(f"What must {frame.unit_name} refine locally without drifting away from the parent intent?")
    return questions


def _has_travel_indicator(request: FragoToConopRequest) -> bool:
    text = " ".join(
        [request.event_type, request.timeframe or "", *request.constraints, *request.support_requirements]
    ).lower()
    return any(term in text for term in {"travel", "movement", "distributed", "overnight", "field", "at "})


def _has_overnight_indicator(request: FragoToConopRequest) -> bool:
    text = " ".join([request.event_type, request.timeframe or "", *request.constraints]).lower()
    return any(term in text for term in {"overnight", "multi-day", "field day plus", "at "})


def _needs_g9(request: FragoToConopRequest) -> bool:
    text = " ".join(
        [
            request.title,
            request.mission_or_training_goal,
            *request.g9_inputs,
            *request.partner_types,
            *request.civil_considerations,
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
