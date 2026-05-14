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
                "public logistics training references",
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
                "maintenance, supply, and friction points. Call out fantasy assumptions early, identify the "
                "longest lead-time item first, and stay advisory."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-4 / logistics advisory draft.\n\n"
            "Use this to shape reserve logistics planning, not as authoritative movement or support direction.\n\n"
            "Bottom line:\n"
            "- If transport, billeting, chow, ammo, comm support, medical support, or accountability is shaky,\n"
            "  the plan is not ready no matter how good it looks on the whiteboard.\n\n"
            "Primary S-4 lenses:\n"
            "- What support must be in place for this event or plan to work at all?\n"
            "- What movement, billeting, chow, comm support, fuel, supply, maintenance, or medical assumptions exist?\n"
            "- What has the longest lead time and therefore needs the earliest decision?\n"
            "- What reserve-specific friction will show up because people, gear, and support are distributed?\n\n"
            "My read:\n"
            "- The hardest logistics problem usually hides in accountability, travel timing,\n"
            "  or late support requests.\n"
            "- Nice ideas die when nobody owns vehicles, billeting, ammo, or issue/turn-in windows.\n\n"
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
            citations=[
                "MCDP 4 Logistics",
                "MCTP 3-40B Tactical Logistics",
                "MCO 3502.8A Marine Corps Logistics Tactics, Training, and Education Program",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCDP 4 Logistics",
                    confidence=Confidence.low,
                    notes="Verify the current public logistics reference before acting.",
                ),
                StructuredCitation(
                    title="MCTP 3-40B Tactical Logistics",
                    confidence=Confidence.low,
                    notes="Use for practical logistics planning and support relationships.",
                ),
                StructuredCitation(
                    title="MCO 3502.8A Marine Corps Logistics Tactics, Training, and Education Program",
                    confidence=Confidence.low,
                    notes="Useful for logistics training expectations and professional development framing.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="MCDP 4 Logistics",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Review the latest verified logistics reference before final planning.",
                ),
                SourceTrustMarker(
                    tracked_title="MCTP 3-40B Tactical Logistics",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current tactical logistics guidance before final support planning.",
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
