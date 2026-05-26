from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import MedicalPlanningRequest, MedicalPlanningResponse


class MedicalPlanner:
    def build(self, request: MedicalPlanningRequest) -> MedicalPlanningResponse:
        medical_support_estimate = [
            f"Supported event: {request.supported_event}",
            "Define the likely casualty profile, treatment capability on hand, and escalation path in plain language.",
            "Treat this as advisory planning support, not as medical direction or credentialed clinical guidance.",
            "Confirm who is actually trained, equipped, and authorized to provide care or make transport decisions.",
            "Write stop-training triggers before the event, not after the first medical inject.",
        ]
        if request.audience:
            medical_support_estimate.append(f"Supported audience / formation: {request.audience}")
        medical_support_estimate.extend(f"Medical-risk context: {item}" for item in request.medical_risk_context)

        tccc_considerations = [
            "Use TCCC as a planning reference for likely trauma priorities, not as a substitute for real training.",
            "Confirm who can address immediate life threats, who carries trauma gear, and where that gear actually is.",
            "Plan transitions from point of injury to higher care without assuming ideal conditions.",
            "Keep training, credentialing, and equipment assumptions explicit.",
        ]
        tccc_knowledge_points = [
            "Refresh TCCC priorities at an awareness level so leaders know what "
            "trained responders are trying to solve first.",
            "Confirm the unit shares a common vocabulary for massive bleeding, "
            "airway, breathing, circulation, and hypothermia concerns.",
            "Distinguish self-aid and buddy-aid expectations from "
            "corpsman-level or higher-care handoff actions.",
            "Verify trauma gear placement, access, and user familiarity "
            "instead of assuming everyone knows where it is.",
        ]

        nine_line_considerations = [
            "Rehearse the 9-line concept as a generic reporting structure "
            "without storing sensitive real-world details.",
            "Confirm who would transmit the request, who validates pickup information, and who receives updates.",
            "Ensure location, pickup, and patient-status reporting methods are understood at a training-safe level.",
            "Do not treat a template as a substitute for qualified medical evacuation procedures or local SOP.",
        ]

        casevac_plan_elements = [
            "Identify likely casualty collection point and transfer points.",
            "Define primary and alternate movement methods for casualty evacuation at a broad planning level.",
            "Clarify who makes the call to move, who coordinates transport, and who maintains accountability.",
            "Tie CASEVAC assumptions to terrain, weather, distance, comm, and vehicle availability.",
        ]
        casevac_plan_elements.extend(f"Casualty scenario to cover: {item}" for item in request.casualty_scenarios)
        casevac_medevac_check = [
            "Name the point-of-injury, casualty collection, transfer, pickup, and higher-care assumptions.",
            "Confirm whether this event is relying on unit CASEVAC, external MEDEVAC support, or both.",
            "State who sends the request, who validates the pickup plan, and "
            "who tracks the casualty after movement starts.",
            "Force primary, alternate, and degraded transport assumptions into the written plan before execution.",
        ]

        casualty_collection_logic = [
            "Define how casualties move from point of injury to a casualty "
            "collection point and then to transport or higher care.",
            "State who secures the scene, who provides first-response care, and who updates accountability.",
            "Keep the casualty collection point tied to terrain, cover, access, supervision, and comm reality.",
            "Identify what condition, distance, or tactical friction would force the collection logic to change.",
        ]

        medical_decision_points = [
            "What casualty threshold, delay, or condition changes the event instead of merely stressing it?",
            "Who can stop, pause, or modify training for medical reasons?",
            "What transport, handoff, or higher-care assumption still requires command visibility?",
            "What must be approved, rehearsed, or verified before the medical plan is treated as executable?",
        ]

        medical_rehearsal_checks = [
            "Rehearse who makes the first casualty call and how that report reaches the decision-maker.",
            "Rehearse casualty collection, movement handoff, and accountability updates at a training-safe level.",
            "Check that trauma gear, transport assumptions, and comm methods match the written plan.",
            "Confirm stop-training triggers are understood by leaders, controllers, and support personnel.",
        ]

        coordination_requirements = [
            "Coordinate with the OIC/RSO or event lead on emergency-action triggers and decision authority.",
            "Coordinate with S-4 or transport support on vehicles, drivers, and movement assumptions.",
            "Coordinate with S-6 on generic comm checks and fallback methods.",
            "Force a yes-or-no answer on casualty movement ownership before execution.",
            "Pause for qualified medical and command review before treating the plan as final.",
        ]
        coordination_trigger_list = [
            "Trigger command review if casualty evacuation timing, transport, or "
            "coverage changes the event's acceptability.",
            "Trigger S-4 coordination when vehicle availability, route access, "
            "or driver coverage weakens casualty movement.",
            "Trigger S-6 coordination when the primary casualty-reporting path, "
            "guard plan, or fallback comm method is weak.",
            "Trigger safety and OIC/RSO review when hazards, tempo, or "
            "environmental conditions outgrow the written controls.",
            "Trigger qualified medical review when the plan assumes treatment "
            "capability, equipment, or credentials not yet confirmed.",
        ]
        if request.travel_required:
            coordination_requirements.append(
                "Travel is in scope; validate how evacuation timelines change "
                "when personnel arrive from distributed locations."
            )
            coordination_trigger_list.append(
                "Trigger coordination early if distributed travel or convoy "
                "movement stretches casualty response timelines."
            )
        if request.overnight:
            coordination_requirements.append(
                "Overnight operations are in scope; confirm watchstanding, rest, "
                "and med-support continuity assumptions."
            )
            coordination_trigger_list.append(
                "Trigger review if overnight coverage, rest cycles, or "
                "watchstanding assumptions reduce medical responsiveness."
            )

        return MedicalPlanningResponse(
            title=f"Medical planning support: {request.title}",
            medical_support_estimate=medical_support_estimate,
            tccc_considerations=tccc_considerations,
            tccc_knowledge_points=tccc_knowledge_points,
            nine_line_considerations=nine_line_considerations,
            casevac_plan_elements=casevac_plan_elements,
            casevac_medevac_check=casevac_medevac_check,
            casualty_collection_logic=casualty_collection_logic,
            medical_decision_points=medical_decision_points,
            medical_rehearsal_checks=medical_rehearsal_checks,
            coordination_requirements=coordination_requirements,
            coordination_trigger_list=coordination_trigger_list,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Medical planning support is advisory only and does not replace qualified medical direction, "
                    "TCCC instruction, evacuation SOP, or local emergency procedures."
                ),
            ],
        )
