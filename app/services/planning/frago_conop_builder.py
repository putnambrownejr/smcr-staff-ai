from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.planning import (
    FragoToConopRequest,
    FragoToConopResponse,
    GuidanceExtraction,
    MetAlignmentItem,
    PlanningApproachAssessment,
    SubordinateConopPacket,
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
    StaffCouncilRequest,
    StaffCouncilResponse,
    StaffEchelon,
)
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.schemas.tdg import TdgGenerationRequest, TdgGenerationResponse
from app.schemas.training import S3PlanningRequest, S3PlanningResponse, S4PlanningRequest, S4PlanningResponse
from app.services.planning.approach import assess_planning_approach
from app.services.staff.council import StaffCouncilService
from app.services.staff.g9_planner import G9Planner
from app.services.staff.medical_planner import MedicalPlanner
from app.services.staff.s2_estimator import S2Estimator
from app.services.staff.s6_planner import S6Planner
from app.services.staff_products.builder import StaffProductBuilder
from app.services.training.s3_planner import S3Planner
from app.services.training.s4_planner import S4Planner
from app.services.training.tdg_builder import TdgBuilder


class FragoToConopBuilder:
    def __init__(self) -> None:
        self._s2 = S2Estimator()
        self._s3 = S3Planner()
        self._s4 = S4Planner()
        self._s6 = S6Planner()
        self._medical = MedicalPlanner()
        self._g9 = G9Planner()
        self._council = StaffCouncilService()
        self._products = StaffProductBuilder()
        self._tdg = TdgBuilder()

    def build(self, request: FragoToConopRequest) -> FragoToConopResponse:
        boundary_warnings = detect_sensitive_input(_request_text(request))
        if boundary_warnings:
            request = _sanitize_frago_request(request)
        parsed_guidance = _extract_guidance(request)
        planning_approach = self._planning_approach(request, parsed_guidance)
        s2_estimate = self._build_s2_estimate(request)
        s3_plan = self._s3.build(
            S3PlanningRequest(
                title=request.title,
                mission_or_training_goal=request.mission_or_training_goal,
                event_type=request.event_type,
                audience=request.supported_unit,
                timeframe=request.timeframe,
                constraints=[*request.constraints, *parsed_guidance.constraints[:2], *request.higher_guidance[:2]],
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
        subordinate_conop_packets = _subordinate_conop_packets(request, relationship_framework, parsed_guidance)
        met_alignment = _met_alignment(request)

        frago_facts = [
            f"Higher headquarters: {request.higher_headquarters}" if request.higher_headquarters else None,
            f"Supported echelon: {request.supported_echelon.value}",
            f"Supported unit: {request.supported_unit}",
            f"Mission/training goal: {request.mission_or_training_goal}",
            *[f"Commander's intent note: {item}" for item in parsed_guidance.commander_intent[:2]],
            f"Recommended planning method: {planning_approach.recommended_method.upper()}",
            f"Planning decision: {planning_approach.decision}",
            *[f"Directed task: {item}" for item in parsed_guidance.directed_tasks[:4]],
            *[f"Constraint: {item}" for item in parsed_guidance.constraints[:3]],
            *[f"Coordinating instruction: {item}" for item in parsed_guidance.coordinating_instructions[:3]],
            *[f"Higher guidance: {item}" for item in request.higher_guidance[:4]],
            *[f"S-3 input: {item}" for item in request.s3_inputs[:3]],
            *[f"G-9 input: {item}" for item in request.g9_inputs[:3]],
        ]
        frago_draft = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.frago,
                topic=request.title,
                audience=request.supported_unit,
                echelon=request.supported_echelon.value,
                preferred_format=request.preferred_format,
                facts=[item for item in frago_facts if item],
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )

        conop_facts = [
            f"Parent concept must support: {request.mission_or_training_goal}",
            f"Supported unit: {request.supported_unit}",
            f"Planning method: {planning_approach.recommended_method.upper()}",
            *[
                f"Subordinate relationship: {frame.unit_name} / {frame.relationship}"
                for frame in relationship_framework
            ],
            *[
                f"Subordinate packet: {packet.unit_name} task is {packet.task_statement}"
                for packet in subordinate_conop_packets[:3]
            ],
            *[f"MET/METL alignment: {item.task_name} ({item.alignment_type})" for item in met_alignment[:4]],
            *[f"Support dependency: {item}" for item in s4_plan.critical_support_requirements[:3]],
        ]
        initial_conop = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.conop,
                topic=f"Initial CONOP for {request.title}",
                audience=request.supported_unit,
                echelon=request.supported_echelon.value,
                preferred_format=request.preferred_format,
                facts=conop_facts,
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )

        tdg_package = self._build_tdg_package(request, parsed_guidance, subordinate_conop_packets)

        aar_facts = [
            f"Supported unit: {request.supported_unit}",
            *[f"Assess against: {item.task_name}" for item in met_alignment[:4]],
            "AAR should read like a staff record of what to preserve, fix, and verify before the next event.",
            "Capture observations by unit/sub-unit, standard, friction point, and corrective action.",
            *(
                [f"Wargame focus: {item}" for item in tdg_package.forced_decision[:2]]
                if tdg_package is not None
                else []
            ),
            *(
                [f"Failure trigger to observe: {item}" for item in tdg_package.failure_triggers[:2]]
                if tdg_package is not None
                else []
            ),
        ]
        aar_framework = self._products.build(
            StaffProductDraftRequest(
                product_type=StaffProductType.aar,
                topic=f"AAR framework for {request.title}",
                audience=request.supported_unit,
                echelon=request.supported_echelon.value,
                facts=aar_facts,
                constraints=request.constraints,
                training_or_fictional=request.training_only,
            )
        )
        xo_sel_review = _xo_sel_review(self._council, request, parsed_guidance)

        return FragoToConopResponse(
            title=f"FRAGO to CONOP package: {request.title}",
            guidance_summary=_guidance_summary(request),
            commander_focus=_commander_focus(request, s3_plan),
            planning_approach=planning_approach,
            parsed_guidance=parsed_guidance,
            unit_relationship_framework=relationship_framework,
            subordinate_conop_packets=subordinate_conop_packets,
            met_alignment=met_alignment,
            initial_conop=initial_conop,
            frago_draft=frago_draft,
            aar_framework=aar_framework,
            tdg_package=tdg_package,
            s2_estimate=s2_estimate,
            s3_plan=s3_plan,
            s4_plan=s4_plan,
            s6_plan=s6_plan,
            medical_plan=medical_plan,
            g9_plan=g9_plan,
            xo_sel_review=xo_sel_review,
            key_assumptions=_key_assumptions(request, parsed_guidance, s4_plan, s6_plan, medical_plan),
            key_risks=_key_risks(s3_plan, s4_plan, s6_plan, medical_plan),
            learning_cycle=_learning_cycle(request, tdg_package),
            det_follow_on_questions=_follow_on_questions(request, relationship_framework, subordinate_conop_packets),
            warnings=[
                *DEFAULT_WARNINGS,
                *boundary_warnings,
                "This FRAGO-to-CONOP package is advisory and must be reviewed by the command and staff chain.",
            ],
        )

    def _planning_approach(
        self,
        request: FragoToConopRequest,
        parsed_guidance: GuidanceExtraction,
    ) -> PlanningApproachAssessment:
        return assess_planning_approach(
            title=request.title,
            mission_or_training_goal=request.mission_or_training_goal,
            event_type=request.event_type,
            timeframe=request.timeframe,
            constraints=[*request.constraints, *parsed_guidance.constraints],
            higher_guidance=[
                *request.higher_guidance,
                *parsed_guidance.commander_intent,
                *parsed_guidance.directed_tasks,
            ],
            coordinating_sections=request.coordinating_sections,
            support_requirements=request.support_requirements,
            partner_types=request.partner_types,
            civil_considerations=[*request.civil_considerations, *request.g9_inputs],
            subordinate_unit_count=len(request.subordinate_units),
            source_items_present=bool(request.source_items or request.intelligence_question),
            formal_event=request.formal_event,
            raw_guidance_text=request.raw_guidance_text,
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

    def _build_tdg_package(
        self,
        request: FragoToConopRequest,
        parsed_guidance: GuidanceExtraction,
        subordinate_conop_packets: list[SubordinateConopPacket],
    ) -> TdgGenerationResponse | None:
        if not request.include_tdg:
            return None
        return self._tdg.build(
            TdgGenerationRequest(
                title=f"{request.title} decision game",
                theme="Command judgment, subordinate nesting, and reserve-friction branch planning",
                audience=request.supported_unit,
                training_objective=(
                    "Force an early command decision, expose weak assumptions, and rehearse branches before "
                    "execution starts burning time."
                ),
                scenario_context=[
                    f"Supported unit: {request.supported_unit}",
                    f"Planning problem: {request.mission_or_training_goal}",
                    *[f"Commander intent note: {item}" for item in parsed_guidance.commander_intent[:2]],
                ],
                opposing_factors=[
                    *parsed_guidance.constraints[:2],
                    *parsed_guidance.assumptions_to_confirm[:2],
                ],
                friendly_forces=[
                    *[
                        f"{packet.unit_name}: {packet.task_statement}"
                        for packet in subordinate_conop_packets[:3]
                    ],
                ],
                civil_considerations=request.civil_considerations[:3],
                reserve_friction=[
                    "Compressed drill timeline",
                    "Distributed Marines and uneven continuity between drill periods",
                    *request.constraints[:2],
                ],
                decision_time="10 minutes for the initial commander decision",
                references=["MCDP 5 Planning", "MCWP 5-10 Marine Corps Planning Process"],
                constraints=[
                    "Training-only framing",
                    "Use realistic reserve friction, not fantasy resourcing.",
                ],
                include_red_team=True,
                include_sketch_map_prompt=True,
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
                    "Translate higher guidance into a Marine-staff concept the company can actually execute.",
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
                subordinate.purpose or "Build a subordinate concept that supports the parent scheme of maneuver.",
                f"On order, {subordinate.unit_name} supports the parent concept without rewriting command intent.",
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


def _subordinate_conop_packets(
    request: FragoToConopRequest,
    relationship_framework: list[UnitRelationshipFrame],
    parsed_guidance: GuidanceExtraction,
) -> list[SubordinateConopPacket]:
    packets: list[SubordinateConopPacket] = []
    for frame in relationship_framework:
        task_statement = _task_statement_for(frame, request, parsed_guidance)
        purpose = _purpose_for(frame, request)
        packets.append(
            SubordinateConopPacket(
                unit_name=frame.unit_name,
                relationship=frame.relationship,
                task_statement=task_statement,
                purpose=purpose,
                concept_focus=[
                    "Support the parent unit's main effort and avoid freelancing the scheme of maneuver.",
                    "Turn parent guidance into a local concept, timeline, and report plan.",
                    *frame.task_focus[:2],
                ],
                command_and_support_relationships=[
                    f"Parent unit: {request.supported_unit}",
                    f"Relationship: {frame.relationship}",
                    *parsed_guidance.command_relationship_notes[:2],
                ],
                required_reports=[
                    "Initial backbrief of local concept and support shortfalls",
                    "Execution-status report by phase or control measure",
                    "AAR input by task, friction point, and corrective action",
                ],
                required_support_requests=frame.support_dependencies[:3],
                aar_focus=[
                    "Did the sub-unit stay nested with the parent intent?",
                    "What support or reporting friction degraded execution first?",
                    "What must the unit carry forward before the next iteration?",
                ],
            )
        )
    return packets


def _met_alignment(request: FragoToConopRequest) -> list[MetAlignmentItem]:
    items: list[MetAlignmentItem] = []
    for task in request.met_tasks:
        items.append(
            MetAlignmentItem(
                task_name=task,
                alignment_type="MET",
                why_it_matters=(
                    "This named task should drive the FRAGO, the subordinate concept, "
                    "and the standard used in the AAR instead of letting activity stand in for readiness."
                ),
                assessment_focus=(
                    "What right looked like, what was observed, "
                    "where the unit drifted, and what must improve before the next iteration."
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
                    "and the commander's priority of effort across the parent and supporting elements."
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
        f"Supported echelon: {request.supported_echelon.value}",
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
        "Decide what conditions trigger the parent unit to cut scope rather than accept a weak execution standard.",
        *s3_plan.command_decision_points[:2],
    ]


def _key_assumptions(
    request: FragoToConopRequest,
    parsed_guidance: GuidanceExtraction,
    s4_plan: S4PlanningResponse,
    s6_plan: S6PlanResponse,
    medical_plan: MedicalPlanningResponse,
) -> list[str]:
    assumptions = [
        "Higher guidance is stable enough to build an initial subordinate concept.",
        "Subordinate units will receive enough clarity to refine their own concepts "
        "instead of guessing command intent.",
        *parsed_guidance.assumptions_to_confirm[:2],
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
    subordinate_conop_packets: list[SubordinateConopPacket],
) -> list[str]:
    questions = [
        "What part of the parent's concept must remain fixed across all subordinate units?",
        "What support shortfall or command relationship still needs clarification "
        "before subordinate concepts can stabilize?",
        "What will the AAR need to compare across units or sub-units?",
    ]
    for frame in relationship_framework[:3]:
        questions.append(f"What must {frame.unit_name} refine locally without drifting away from the parent intent?")
    for packet in subordinate_conop_packets[:2]:
        questions.append(f"What support or reporting burden will break {packet.unit_name}'s concept first?")
    return questions


def _learning_cycle(
    request: FragoToConopRequest,
    tdg_package: TdgGenerationResponse | None,
) -> list[str]:
    cycle = [
        "Start with higher guidance and lock the parent FRAGO to command intent, support reality, and named standards.",
        "Push subordinate units to refine local concepts without rewriting the parent problem.",
    ]
    if tdg_package is not None:
        cycle.extend(
            [
                (
                    "Run the linked TDG or short wargame before execution to force the commander "
                    "decision and expose the branch point."
                ),
                "Use the TDG failure triggers and forced decisions as watch items during execution and in the AAR.",
            ]
        )
    cycle.append(
        "Write the AAR against the standard, the decision made, the friction observed, and the "
        "corrective action for the next iteration."
    )
    if request.formal_event:
        cycle.append("Keep XO/SEL review tied to the same chain so standards and sequence survive into execution.")
    return cycle


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


def _extract_guidance(request: FragoToConopRequest) -> GuidanceExtraction:
    directed_tasks: list[str] = []
    constraints: list[str] = list(request.constraints)
    coordinating_instructions: list[str] = []
    command_relationship_notes: list[str] = []
    assumptions_to_confirm: list[str] = []
    commander_intent: list[str] = []

    guidance_items = [*request.higher_guidance, *request.frago_facts]
    if request.raw_guidance_text:
        guidance_items.extend(
            line.strip(" -\t")
            for line in request.raw_guidance_text.splitlines()
            if line.strip()
        )

    for item in guidance_items:
        lower = item.lower()
        if any(term in lower for term in {"intent", "purpose", "end state", "main effort"}):
            commander_intent.append(item)
        if any(term in lower for term in {"task", "conduct", "execute", "provide", "submit", "be prepared to"}):
            directed_tasks.append(item)
        if any(term in lower for term in {"constraint", "limit", "only", "must not", "no later than", "nlt"}):
            constraints.append(item)
        if any(term in lower for term in {"report", "coordinate", "timeline", "control measure", "check-in"}):
            coordinating_instructions.append(item)
        if any(term in lower for term in {"attached", "detached", "supporting", "supported", "opcON", "tacon"}):
            command_relationship_notes.append(item)
        if any(term in lower for term in {"assume", "pending", "subject to", "to be confirmed", "tentative"}):
            assumptions_to_confirm.append(item)

    if not commander_intent:
        commander_intent.append(
            "Treat the commander's intent as: protect the training standard, "
            "keep subordinate effort nested, and cut what cannot be resourced."
        )
    if not directed_tasks:
        directed_tasks.extend(
            [
                "Translate higher guidance into a parent FRAGO with clear subordinate tasks and support requirements.",
                "Require each subordinate unit to refine a local concept without rewriting command intent.",
            ]
        )
    if not coordinating_instructions:
        coordinating_instructions.append(
            "Publish reporting windows, support shortfalls, and the backbrief point for subordinate concepts."
        )
    if not command_relationship_notes:
        command_relationship_notes.append(
            "Confirm supported, supporting, attached, and parent-child "
            "relationships before execution products are treated as final."
        )
    if not assumptions_to_confirm:
        assumptions_to_confirm.append(
            "Verify what higher guidance, support availability, and subordinate "
            "readiness assumptions are still unconfirmed."
        )

    return GuidanceExtraction(
        commander_intent=commander_intent[:3],
        directed_tasks=directed_tasks[:6],
        constraints=list(dict.fromkeys(constraints))[:5],
        coordinating_instructions=coordinating_instructions[:5],
        command_relationship_notes=command_relationship_notes[:4],
        assumptions_to_confirm=assumptions_to_confirm[:4],
    )


def _task_statement_for(
    frame: UnitRelationshipFrame,
    request: FragoToConopRequest,
    parsed_guidance: GuidanceExtraction,
) -> str:
    if frame.relationship in {"supported", "main effort"}:
        return (
            f"On order, {frame.unit_name} is the supported effort for {request.title} and conducts the decisive action "
            "required to meet the parent unit's training objective."
        )
    if frame.relationship in {"supporting", "attached"}:
        return (
            f"On order, {frame.unit_name} supports {request.supported_unit} "
            "by providing the required reports, support, "
            "or local execution actions needed to keep the parent concept moving."
        )
    if parsed_guidance.directed_tasks:
        return (
            f"On order, {frame.unit_name} executes its assigned portion of the "
            f"parent concept and supports: {parsed_guidance.directed_tasks[0]}"
        )
    return (
        f"On order, {frame.unit_name} refines and executes a local concept "
        f"nested with {request.supported_unit}'s FRAGO and command intent."
    )


def _purpose_for(frame: UnitRelationshipFrame, request: FragoToConopRequest) -> str:
    return (
        f"Purpose: ensure {frame.unit_name} contributes directly to {request.mission_or_training_goal} "
        "without drifting from the parent unit's standard or reporting scheme."
    )


def _xo_sel_review(
    council: StaffCouncilService,
    request: FragoToConopRequest,
    parsed_guidance: GuidanceExtraction,
) -> StaffCouncilResponse | None:
    if not _needs_formal_event_review(request, parsed_guidance):
        return None

    roles = ["xo", "firstsgt"] if request.supported_echelon == StaffEchelon.company else ["xo", "sgtmaj"]
    return council.vet_idea(
        StaffCouncilRequest(
            question=(
                f"Review this formal event or standards-heavy package for {request.supported_unit}. "
                "Focus on feasibility, sequence control, accountability, "
                "public-facing discipline, and release criteria."
            ),
            echelon=request.supported_echelon,
            roles=roles,
            context={
                "formal_event": True,
                "supported_unit": request.supported_unit,
                "title": request.title,
                "parsed_guidance": parsed_guidance.model_dump(),
            },
        )
    )


def _needs_formal_event_review(request: FragoToConopRequest, parsed_guidance: GuidanceExtraction) -> bool:
    if request.formal_event:
        return True
    text = " ".join(
        [
            request.title,
            request.event_type,
            request.mission_or_training_goal,
            *(request.higher_guidance),
            *(parsed_guidance.coordinating_instructions),
            *(request.constraints),
        ]
    ).lower()
    return any(
        term in text
        for term in {
            "ceremony",
            "change of command",
            "memorial",
            "birthday ball",
            "formal",
            "public-facing",
            "review",
            "parade",
            "honors",
            "protocol",
        }
    )


def _request_text(request: FragoToConopRequest) -> str:
    return " ".join(
        [
            request.title,
            request.supported_unit,
            request.event_type,
            request.mission_or_training_goal,
            request.raw_guidance_text or "",
            request.intelligence_question or "",
            request.timeframe or "",
            *request.higher_guidance,
            *request.frago_facts,
            *request.s3_inputs,
            *request.g9_inputs,
            *request.met_tasks,
            *request.metl_focus,
            *request.constraints,
            *request.support_requirements,
            *request.coordinating_sections,
            *request.partner_types,
            *request.civil_considerations,
            *request.medical_risk_context,
            *request.casualty_scenarios,
            *[str(item) for item in request.source_items],
        ]
    )


def _sanitize_frago_request(request: FragoToConopRequest) -> FragoToConopRequest:
    return request.model_copy(
        update={
            "title": "Sensitive FRAGO request withheld",
            "supported_unit": "Supported unit withheld",
            "mission_or_training_goal": (
                "Provide only a generic training-only FRAGO/CONOP scaffold and route specific details through "
                "approved channels."
            ),
            "raw_guidance_text": None,
            "higher_guidance": ["Sensitive operational guidance withheld."],
            "frago_facts": [],
            "s3_inputs": [],
            "g9_inputs": [],
            "source_items": [],
            "intelligence_question": None,
            "subordinate_units": [],
            "met_tasks": [],
            "metl_focus": [],
            "constraints": ["Sensitive operational details were withheld."],
            "support_requirements": [],
            "coordinating_sections": [],
            "partner_types": [],
            "civil_considerations": [],
            "medical_risk_context": ["Use generic training-safe medical planning only."],
            "casualty_scenarios": ["Generic training injury scenario only."],
            "timeframe": None,
            "formal_event": False,
            "training_only": True,
        }
    )
