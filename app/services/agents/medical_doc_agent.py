from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class MedicalDocAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="medical-doc-advisor",
            name="Medical / Doc Advisor",
            description=(
                "Supports training-safe CASEVAC planning, TCCC-aware risk framing, 9-line familiarity, and "
                "medical-support coordination without claiming clinical authority."
            ),
            domain="medical support",
            intended_users=["SMCR officers", "Doc", "corpsman support planners", "S-3", "OIC", "command teams"],
            allowed_sources=[
                "public TCCC references",
                "public health service support doctrine",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "real patient records",
                "private medical details",
                "requests for diagnosis or treatment decisions",
                "sensitive real-world medevac details in unapproved environments",
            ],
            system_prompt=(
                "Respond like a practical field medical planner or doc supporting training and staff planning. "
                "Focus on CASEVAC structure, TCCC-aware planning, and coordination. Stay advisory and require "
                "qualified medical review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Medical / Doc advisory draft.\n\n"
            "Use this to shape training-safe medical support and CASEVAC planning, not as clinical direction.\n\n"
            "Primary medical-support lenses:\n"
            "- What casualty risks are actually plausible for this event or field problem?\n"
            "- Who is qualified, equipped, and positioned to address immediate life threats?\n"
            "- What assumptions exist about TCCC familiarity, evacuation timing, and transport availability?\n"
            "- What needs to be rehearsed at a generic 9-line / CASEVAC level before the event starts?\n\n"
            "Checklist:\n"
            "- Define likely casualty scenarios and who owns first response actions.\n"
            "- Confirm trauma gear, casualty collection, transport, and handoff assumptions.\n"
            "- Rehearse 9-line familiarity and reporting flow at a training-safe level only.\n"
            "- Tie CASEVAC planning to terrain, distance, comm, vehicles, and command decision points.\n"
            "- Pause for qualified medical review before treating the plan as final.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "Public TCCC references",
                "Public health service support doctrine",
                "Operations planning references",
            ],
            structured_citations=[
                StructuredCitation(
                    title="Public TCCC references",
                    confidence=Confidence.low,
                    notes="Use for training awareness and planning only; not a substitute for formal instruction.",
                ),
                StructuredCitation(
                    title="Public health service support doctrine",
                    confidence=Confidence.low,
                    notes="Verify the current public health-service-support reference before acting.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Public TCCC references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm the latest verified training-safe TCCC reference before building event guidance.",
                ),
                SourceTrustMarker(
                    tracked_title="Public health service support doctrine",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Verify the current public doctrine before relying on medical-support assumptions.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a field event, range, convoy, or general training problem?",
                "What casualty scenarios are most likely enough to drive planning?",
                "Who is the qualified medical reviewer for this plan?",
            ],
        )


def build_medical_doc_agent() -> MedicalDocAdvisorAgent:
    return MedicalDocAdvisorAgent()
