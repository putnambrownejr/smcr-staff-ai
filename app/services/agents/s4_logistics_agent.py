from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class S4LogisticsAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s4-logistics",
            name="S-4 / Logistics Advisor",
            description=(
                "Supports reserve logistics planning, movement, sustainment, supply, maintenance, and "
                "supportability checks for staff planning."
            ),
            domain="logistics",
            intended_users=["SMCR officers", "S-4", "LogO", "S-3", "Chief of Staff / Aide"],
            allowed_sources=[
                "public logistics doctrine",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified movement plans",
                "sensitive supply or transport details",
                "real-world exact convoy or sustainment details in unapproved environments",
            ],
            system_prompt=(
                "Respond like a practical reserve S-4/LogO. Focus on supportability, sustainment, movement, "
                "maintenance, supply, and friction points. Stay advisory and require human review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-4 / logistics advisory draft.\n\n"
            "Use this to shape reserve logistics planning, not as authoritative movement or support direction.\n\n"
            "Primary S-4 lenses:\n"
            "- What support must be in place for this event or plan to work at all?\n"
            "- What movement, billeting, chow, comm support, fuel, supply, maintenance, or medical assumptions exist?\n"
            "- What has the longest lead time and therefore needs the earliest decision?\n"
            "- What reserve-specific friction will show up because people, gear, and support are distributed?\n\n"
            "Checklist:\n"
            "- Identify critical support requirements, lead times, and approval points.\n"
            "- Separate must-have sustainment from nice-to-have convenience requests.\n"
            "- Confirm transport, billeting, equipment, and accountability assumptions.\n"
            "- Flag maintenance, ammo, communications, and medical dependencies early.\n"
            "- Build follow-up actions with owners and suspense dates before leaving drill.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=["Marine Corps logistics doctrine", "Operations planning references"],
            structured_citations=[
                StructuredCitation(
                    title="Marine Corps logistics doctrine",
                    confidence=Confidence.low,
                    notes="Verify the current public logistics reference before acting.",
                ),
                StructuredCitation(
                    title="Operations planning references",
                    confidence=Confidence.low,
                    notes="Confirm current planning references before integrating logistics assumptions.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Marine Corps logistics doctrine",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Review the latest verified logistics reference before final planning.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a drill, AT, range, convoy, or field-support problem?",
                "What support item or lead time is most likely to break the plan first?",
                "Which sections need to coordinate for this to become supportable?",
            ],
        )


def build_s4_logistics_agent() -> S4LogisticsAdvisorAgent:
    return S4LogisticsAdvisorAgent()
