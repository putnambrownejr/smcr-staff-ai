from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class AirOAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="airo-advisor",
            name="AirO Advisor",
            description=(
                "Supports reserve-focused aviation coordination, air support planning questions, and "
                "air-ground integration checklists for staff planning."
            ),
            domain="aviation support",
            intended_users=["AirO", "S-3", "staff officers", "command teams"],
            allowed_sources=[
                "public aviation support doctrine",
                "public operations-planning doctrine",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "real current air tasking details",
                "classified aviation operations",
                "exact movements or sensitive aviation coordination data",
            ],
            system_prompt=(
                "Provide advisory air-support planning and coordination checklists "
                "for training or public planning contexts. Stay generic and require human review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "AirO advisory draft.\n\n"
            "Use this to shape air-support coordination and planning, not as authoritative tasking "
            "or aviation direction.\n\n"
            "Primary AirO lenses:\n"
            "- What air support effect is actually needed, and what decision does that support?\n"
            "- What coordination must happen between operations, fires, comm, safety, and supported ground elements?\n"
            "- What assumptions about timing, support availability, and deconfliction need review?\n"
            "- What parts of the request should remain generic until validated through the proper channels?\n\n"
            "Checklist:\n"
            "- Define the supported event, desired effect, and supported unit/task.\n"
            "- Identify required coordination points, support requests, and deconfliction questions.\n"
            "- Confirm comm, ORM, and control relationships at a generic planning level only.\n"
            "- Separate training assumptions from real-world support requirements.\n"
            "- Pause for qualified aviation and command review before treating the plan as final.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=["Marine Corps aviation support doctrine", "Operations planning references"],
            structured_citations=[
                StructuredCitation(
                    title="Marine Corps aviation support doctrine",
                    confidence=Confidence.low,
                    notes="Verify current public aviation-support doctrine before use.",
                ),
                StructuredCitation(
                    title="Operations planning references",
                    confidence=Confidence.low,
                    notes="Confirm current planning references before integrating air-support assumptions.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Marine Corps aviation support doctrine",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Check current aviation-support references before final planning.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a training event, exercise support problem, or planning estimate?",
                "What supported effect or decision are you trying to enable?",
                "Which staff sections must coordinate before this becomes a real request?",
            ],
        )


def build_airo_agent() -> AirOAdvisorAgent:
    return AirOAdvisorAgent()
