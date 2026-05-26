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
        if request.travel_required:
            coordination_requirements.append(
                "Travel is in scope; validate how evacuation timelines change "
                "when personnel arrive from distributed locations."
            )
        if request.overnight:
            coordination_requirements.append(
                "Overnight operations are in scope; confirm watchstanding, rest, "
                "and med-support continuity assumptions."
            )

        return MedicalPlanningResponse(
            title=f"Medical planning support: {request.title}",
            medical_support_estimate=medical_support_estimate,
            tccc_considerations=tccc_considerations,
            nine_line_considerations=nine_line_considerations,
            casevac_plan_elements=casevac_plan_elements,
            medical_decision_points=medical_decision_points,
            medical_rehearsal_checks=medical_rehearsal_checks,
            coordination_requirements=coordination_requirements,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Medical planning support is advisory only and does not replace qualified medical direction, "
                    "TCCC instruction, evacuation SOP, or local emergency procedures."
                ),
            ],
        )
