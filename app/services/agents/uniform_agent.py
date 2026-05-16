from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    UNIFORM_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class UniformAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="uniform-advisor",
            name="Uniform Advisor Agent",
            description="Provides advisory uniform-prep and standards guidance grounded in public regulations.",
            domain="uniforms",
            intended_users=["SMCR Marines", "staff officers", "SEL", "command teams"],
            allowed_sources=["public uniform regulations", "public uniform board references", "public MARADMINs"],
            disallowed_inputs=[
                "disciplinary PII",
                "private personnel records",
                "official command authority impersonation",
            ],
            system_prompt=(
                "Provide Marine Corps uniform standards guidance in an advisory tone. Focus on preparation, "
                "serviceability, and ambiguity reduction. Require chain-of-command review for edge cases."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Uniform advisory draft.\n\n"
            "Use this to shape preparation and standards checks, not to override current command guidance.\n\n"
            "Primary uniform lenses:\n"
            "- What event, formation, or ceremony is driving the uniform question?\n"
            "- What part of the standard is clear, and what part still needs command or SEL verification?\n"
            "- What can be fixed before drill instead of discovered at formation?\n\n"
            "My read:\n"
            "- Uniform problems are usually preparation problems first.\n"
            "- If the event uniform, seasonal requirement, or local expectation is vague, fix that early.\n"
            "- Ambiguous wear questions should be routed before event day, not argued on the deck.\n\n"
            "Checklist:\n"
            "- Confirm the event uniform and whether local command guidance changes anything.\n"
            "- Check serviceability, fit, grooming, and required accessories before movement.\n"
            "- Separate black-and-white regulation issues from local execution questions.\n"
            "- Route edge cases to the chain of command or SEL for final clarification.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(UNIFORM_REFERENCES),
            structured_citations=structured_citations(UNIFORM_REFERENCES),
            source_trust=source_trust_markers(
                UNIFORM_REFERENCES,
                notes_prefix=(
                    "Verify the current regulation version and local command guidance "
                    "before final wear decisions."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What event or evolution is driving the uniform question?",
                "Is there local command guidance or a seasonal variation that needs to be checked?",
                "What ambiguity should be routed now so it does not become a formation problem later?",
            ],
        )


def build_uniform_agent() -> UniformAdvisorAgent:
    return UniformAdvisorAgent()
