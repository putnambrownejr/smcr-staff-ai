from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    OPORD_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class DoctrineOpordAssistant(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="doctrine-opord-assistant",
            name="Doctrine / OPORD Assistant",
            description="Provides public-doctrine-grounded OPORD, FRAGO, and order-discipline planning guidance.",
            domain="operations planning",
            intended_users=["staff officers", "commanders", "S-3", "XO"],
            allowed_sources=["public doctrine", "training-only scenarios", "public staff-planning references"],
            disallowed_inputs=["real-world current operations", "classified plans", "exact movements"],
            system_prompt=(
                "Provide Marine-staff order discipline, not authoritative orders. Focus on five-paragraph logic, "
                "command relationships, annex triggers, and what must be explicit before routing."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Doctrine / OPORD advisory draft.\n\n"
            "Use this to shape order logic and staff-product discipline, not as an authoritative operations order.\n\n"
            "Primary OPORD lenses:\n"
            "- What is commander's intent, what is directed, and what must subordinate units refine?\n"
            "- What assumptions, command relationships, and coordinating instructions still need to be made explicit?\n"
            "- What belongs in the base order versus an annex, tab, or rehearsal script?\n\n"
            "My read:\n"
            "- Most weak orders fail because they confuse purpose, task, and support relationships.\n"
            "- If a staff product cannot survive handoff to a subordinate unit, it is not ready to route.\n"
            "- Good FRAGOs cut ambiguity; they do not decorate it.\n\n"
            "Checklist:\n"
            "- Clarify whether this is an OPORD, WARNO, FRAGO, CONOP, or supporting enclosure.\n"
            "- Separate mission, execution concept, sustainment, and command-and-signal responsibilities.\n"
            "- Name what is directed now and what subordinate elements are expected to refine.\n"
            "- Identify required reports, branch decisions, and likely annexes.\n"
            "- Treat this as a draft until command review, source verification, and final routing are complete.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(OPORD_REFERENCES),
            structured_citations=structured_citations(OPORD_REFERENCES),
            source_trust=source_trust_markers(
                OPORD_REFERENCES,
                notes_prefix=(
                    "Verify current doctrine and command applicability before treating any "
                    "order language as final."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this best framed as an OPORD, WARNO, FRAGO, or initial CONOP?",
                "What subordinate units or supporting relationships must the draft preserve?",
                "What decision or ambiguity would most weaken this product if it stayed unresolved?",
            ],
        )


def build_opord_agent() -> DoctrineOpordAssistant:
    return DoctrineOpordAssistant()
