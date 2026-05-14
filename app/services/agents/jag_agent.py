from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class JagLegalAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="jag-legal-advisor",
            name="JAG / Legal Advisor",
            description=(
                "Supports issue-spotting, routing questions, and legal-review prompts for staff work while "
                "clearly refusing to provide legal advice or replace a licensed attorney."
            ),
            domain="legal support",
            intended_users=["command teams", "staff officers", "Chief of Staff / Aide"],
            allowed_sources=[
                "public policy references",
                "public administrative-law references",
                "training-only staff scenarios",
            ],
            disallowed_inputs=[
                "attorney-client privileged content",
                "ongoing investigations with protected details",
                "requests for authoritative legal advice",
                "classified or CUI legal matters in public tooling",
            ],
            system_prompt=(
                "Provide advisory issue-spotting and escalation guidance only. Do not give legal advice. "
                "Direct the user to the proper judge advocate or legal office for authoritative counsel."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "JAG / legal advisory draft.\n\n"
            "This is not legal advice and does not replace a judge advocate, attorney, or official legal review.\n\n"
            "Use this for issue spotting only:\n"
            "- Clarify what decision, action, or command question is driving the legal concern.\n"
            "- Identify whether the matter sounds administrative, fiscal, ethics-related,\n"
            "  investigative, or operational.\n"
            "- Separate public-policy questions from case-specific facts that should go directly to legal counsel.\n"
            "- Preserve only minimum needed context and route protected details through proper channels.\n\n"
            "Recommended next step:\n"
            "- Write a short issue statement, identify the decision deadline, list relevant public references, "
            "and send the matter to the proper legal office for review.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=["Public legal/policy references", "Administrative policy references"],
            structured_citations=[
                StructuredCitation(
                    title="Public legal/policy references",
                    confidence=Confidence.low,
                    notes="Use only as a prompt for issue spotting; obtain real legal review.",
                )
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Public legal/policy references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Public references do not replace formal legal review.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What decision or action deadline is driving the question?",
                "Is this a public-policy question or a case-specific legal matter?",
                "What proper legal office should review this before action?",
            ],
        )


def build_jag_agent() -> JagLegalAdvisorAgent:
    return JagLegalAdvisorAgent()
