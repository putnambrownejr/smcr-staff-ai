from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class S6CommunicationsAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s6-comms",
            name="S-6 / Communications Advisor",
            description=(
                "Supports reserve C2 support planning, PACE framing, supportability checks, and "
                "communications coordination while refusing sensitive technical detail."
            ),
            domain="communications support",
            intended_users=["SMCR officers", "S-6", "CommO", "OpsO", "command teams"],
            allowed_sources=[
                "public communications doctrine",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "COMSEC",
                "keying material",
                "real frequencies",
                "sensitive network data",
                "call signs",
            ],
            system_prompt=(
                "Respond like a practical reserve S-6. Focus on C2 support, PACE planning, supportability, and "
                "permissions while refusing sensitive technical details."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-6 advisory draft.\n\n"
            "Use this to shape communications support and C2 planning, not as authoritative technical direction.\n\n"
            "Primary S-6 lenses:\n"
            "- What communications support is essential to command and control?\n"
            "- What assumptions exist about equipment, permissions, training currency, and support windows?\n"
            "- What fallback methods are available if the preferred plan degrades?\n"
            "- What should remain generic until validated through proper channels?\n\n"
            "Checklist:\n"
            "- Define the supported event and essential C2 effect.\n"
            "- Build a generic PACE planning frame without real frequencies or sensitive identifiers.\n"
            "- Check equipment access, licensing, permissions, and training currency early.\n"
            "- Identify follow-up actions with owners before leaving drill.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=["Public communications doctrine", "Operations planning references"],
            structured_citations=[
                StructuredCitation(
                    title="Public communications doctrine",
                    confidence=Confidence.low,
                    notes="Verify current public communications references before acting.",
                )
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Public communications doctrine",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Check current public communications guidance before finalizing support assumptions.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What supported event or commander decision needs communications support?",
                "What reserve friction matters most here: equipment, permissions, support time, or training currency?",
                "What generic fallback methods exist if the primary approach fails?",
            ],
        )


def build_s6_comms_agent() -> S6CommunicationsAdvisorAgent:
    return S6CommunicationsAdvisorAgent()
