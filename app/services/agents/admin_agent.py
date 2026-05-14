from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.services.agents.base import Agent, AgentContext


class AdminReadinessAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="admin-readiness-advisor",
            name="Admin Readiness Advisor",
            description=(
                "Supports AdminO / S-1 style reserve administration planning, due-outs, readiness references, "
                "orders/DTS continuity, and FitRep-adjacent workflow support."
            ),
            domain="administration",
            intended_users=["SMCR officers", "AdminO", "S-1", "Chief of Staff / Aide", "command teams"],
            allowed_sources=[
                "public MCRAMM / reserve administration references",
                "public PES / FitRep references",
                "public correspondence guidance",
                "local handoff and personal document summaries",
            ],
            disallowed_inputs=[
                "SSNs",
                "full personnel files",
                "medical details beyond minimum readiness tracking",
                "classified or CUI personnel actions in unapproved environments",
            ],
            system_prompt=(
                "Provide advisory admin-readiness checklists, due-out structure, and continuity support. "
                "Do not make official personnel decisions or claim authoritative command guidance."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Admin readiness advisory draft.\n\n"
            "Use this to organize reserve administration work, not as official guidance.\n\n"
            "AdminO / S-1 focus areas:\n"
            "- Confirm current orders, RQS/BIO support references, and contact continuity.\n"
            "- Track FitRep occasions, due dates, RS/RO coordination, and required inputs.\n"
            "- Track DTS authorizations, vouchers, receipts, and follow-up suspense items.\n"
            "- Watch medical/dental readiness references needed for drill, AT, or mobilization prep.\n"
            "- Keep correspondence and routing products aligned with current DON and USMC formatting guidance.\n"
            "- Use local handoff and personal document summaries to reduce missed admin due-outs between drills.\n\n"
            "Suggested checklist:\n"
            "- Identify the suspense, owner, and supporting reference for each admin task.\n"
            "- Separate what is due now from what only needs continuity tracking.\n"
            "- Confirm which items require an official admin chief, S-1, or commander review.\n"
            "- Keep local support files minimal, current, and clearly advisory.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "MCRAMM / reserve administration source stack",
                "PES / FitRep source stack",
                "DON correspondence guidance",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCRAMM / Reserve Administration references",
                    confidence=Confidence.low,
                    notes="Manifest/source-note citation placeholder; verify current public source before use.",
                ),
                StructuredCitation(
                    title="PES / FitRep references",
                    confidence=Confidence.low,
                    notes="Manifest/source-note citation placeholder; verify current MCPEL status before use.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What admin suspense or due-out is driving this request?",
                "Which local references are already stored: RQS, orders, DTS, FitRep, or readiness docs?",
                "Is this a continuity tracker, a checklist request, or a draft routing product?",
            ],
        )


def build_admin_readiness_agent() -> AdminReadinessAdvisorAgent:
    return AdminReadinessAdvisorAgent()
