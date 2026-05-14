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
                "communications coordination while refusing sensitive technical detail. Includes PKI/CAC "
                "troubleshooting as an S-6 user-access support lane."
            ),
            domain="communications support",
            intended_users=["SMCR officers", "S-6", "CommO", "OpsO", "command teams"],
            allowed_sources=[
                "public communications doctrine",
                "public command and control references",
                "public communications training references",
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
                "Respond like a practical reserve S-6. Focus on C2 support, PACE planning, supportability, "
                "permissions, and information flow while refusing sensitive technical details. Treat PKI, CAC, "
                "middleware, and portal access issues as part of the S-6 user-support lane. Be blunt about what "
                "will fail first."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-6 advisory draft.\n\n"
            "Use this to shape communications support and C2 planning, not as authoritative technical direction.\n\n"
            "Bottom line:\n"
            "- If nobody knows how the unit will pass information when the primary method fails,\n"
            "  then the comm plan is decorative, not real.\n\n"
            "Primary S-6 lenses:\n"
            "- What communications support is essential to command and control?\n"
            "- What assumptions exist about equipment, permissions, training currency, and support windows?\n"
            "- What fallback methods are available if the preferred plan degrades?\n"
            "- What user-access risks exist around CAC, PKI, middleware, browser auth, or portal readiness?\n"
            "- What should remain generic until validated through proper channels?\n\n"
            "My read:\n"
            "- In reserve units, the quiet killers are access, permissions, stale gear, and lack of rehearsal.\n"
            "- Keep the plan commercial/training-safe, simple enough to brief, and easy enough to rehearse.\n\n"
            "Checklist:\n"
            "- Define the supported event and essential C2 effect.\n"
            "- Build a generic PACE planning frame without real frequencies or sensitive identifiers.\n"
            "- Identify what information must move, who must receive it, and how long delay is acceptable.\n"
            "- Check equipment access, licensing, permissions, and training currency early.\n"
            "- Treat CAC, certificate, middleware, and portal access issues as S-6 support problems.\n"
            "- Escalate to a local help desk or enterprise support channel when needed.\n"
            "- Identify follow-up actions with owners before leaving drill.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "MCDP 6 Command and Control",
                "MCTP 3-30B Information Management",
                "NAVMC 3500.56C Communications Training and Readiness Manual",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCDP 6 Command and Control",
                    confidence=Confidence.low,
                    notes="Grounds command-and-control thinking at the doctrinal level.",
                ),
                StructuredCitation(
                    title="MCTP 3-30B Information Management",
                    confidence=Confidence.low,
                    notes="Useful for information flow, staff processes, and information-management discipline.",
                ),
                StructuredCitation(
                    title="NAVMC 3500.56C Communications Training and Readiness Manual",
                    confidence=Confidence.low,
                    notes="Use for communications training standards and readiness framing.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="MCDP 6 Command and Control",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Check current public communications guidance before finalizing support assumptions.",
                ),
                SourceTrustMarker(
                    tracked_title="NAVMC 3500.56C Communications Training and Readiness Manual",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current communications training standards before finalizing the support plan.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What supported event or commander decision needs communications support?",
                "What reserve friction matters most here: equipment, permissions, support time, or training currency?",
                "Is there a CAC, certificate, or portal-access issue that should be handled in the S-6 lane first?",
                "What generic fallback methods exist if the primary approach fails?",
            ],
        )


def build_s6_comms_agent() -> S6CommunicationsAdvisorAgent:
    return S6CommunicationsAdvisorAgent()
