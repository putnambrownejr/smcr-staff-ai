from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MARADMIN_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MaradminMonitorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="maradmin-monitor",
            name="MARADMIN Monitor Agent",
            description="Summarizes public MARADMIN and doctrine-index relevance for reserve staff awareness.",
            domain="administration",
            intended_users=["SMCR officers", "staff officers", "admin staff"],
            allowed_sources=["official Marine Corps public releases", "MARADMIN index", "MCPEL index"],
            disallowed_inputs=["PII", "classified information", "unit-sensitive plans"],
            system_prompt=(
                "Monitor public administrative messages and doctrine indexes in an advisory way. Focus on audience, "
                "effective date, likely staff action, and what still needs human review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MARADMIN monitor advisory draft.\n\n"
            "Use this to shape public-message triage and relevance tagging, "
            "not as an authoritative release decision.\n\n"
            "Primary MARADMIN lenses:\n"
            "- Who is the real audience and what action, if any, should they take?\n"
            "- What date, suspense, or policy change actually matters to the staff?\n"
            "- Is the message current, superseded, or still waiting for source verification?\n\n"
            "My read:\n"
            "- The first mistake is treating every MARADMIN like it matters equally.\n"
            "- The second mistake is assuming a summary is enough without checking the actual message text.\n"
            "- Good triage separates awareness, required action, and future watch items.\n\n"
            "Checklist:\n"
            "- Confirm the source is official and the message is still current.\n"
            "- Tag audience, effective date, and whether it affects reserve admin, training, uniform, or PME lanes.\n"
            "- List the staff follow-up actions and who should review them.\n"
            "- Treat local summaries as advisory until the underlying message is checked directly.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MARADMIN_REFERENCES),
            structured_citations=structured_citations(MARADMIN_REFERENCES),
            source_trust=source_trust_markers(
                MARADMIN_REFERENCES,
                notes_prefix="Verify current message text and publication freshness before acting on a summary.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a MARADMIN-awareness problem, a doctrine freshness problem, or both?",
                "Who is the affected audience and what decision or action might this message drive?",
                "Has the underlying message text been checked directly yet?",
            ],
        )


def build_maradmin_agent() -> MaradminMonitorAgent:
    return MaradminMonitorAgent()
