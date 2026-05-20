from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_0202_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosIntel0202AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-intel-0202",
            name="MOS 0202 / Intelligence Officer Advisor",
            description=(
                "Supports the S-2 lane with MOS-aware 0202 advisory help for staff estimates, intelligence "
                "support to planning, collection discipline, and reserve continuity."
            ),
            domain="intelligence support",
            intended_users=["Intelligence officers", "S-2 staff", "planners", "SMCR officers"],
            allowed_sources=[
                "public intelligence doctrine",
                "public intelligence training references",
                "public officer career references",
                "public-source context references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified intelligence",
                "collection tasking against real targets",
                "sources and methods",
                "sensitive real-world named-person reporting",
            ],
            system_prompt=(
                "Respond like a reserve 0202 working under the S-2. Act like the narrower intelligence-officer "
                "slice of the broader S-2 picture. Focus on staff estimates, PIR framing, collection discipline, "
                "assessment quality, and what the commander actually needs to decide."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 0202 intelligence officer advisory draft under the S-2 lane.\n\n"
            "Use this to shape intelligence support to planning, not as authoritative intelligence production.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-2 owns the broad intelligence picture, current reporting, and command-support estimate.\n"
            "- The 0202 lane owns the narrower officer judgment on PIR framing, collection discipline, estimate "
            "quality, and whether the staff is asking the right intelligence question.\n\n"
            "What the MOS lane should add beyond the broad S-2 picture:\n"
            "- a harder read on whether the intelligence question is tied to a real command decision\n"
            "- whether collection, analysis, and briefing effort are being wasted on trivia\n"
            "- whether assumptions, gaps, and confidence are visible enough for the XO and commander\n"
            "- whether continuity notes will let the next drill pick the estimate back up fast\n\n"
            "My read:\n"
            "- Good 0202 work is not impressive trivia. It is disciplined decision support.\n"
            "- Thin-bench reserve staffs drift into background summaries when they should be clarifying what matters "
            "for the next decision.\n"
            "- If confidence, gaps, and sourcing are unclear, the estimate is still soft even if it sounds "
            "polished.\n\n"
            "0202 checklist:\n"
            "- State the command question, the intelligence question, and the decision it supports.\n"
            "- Separate knowns, assessed judgments, assumptions, and gaps.\n"
            "- Identify the PIR-style points that actually matter for planning or execution.\n"
            "- Keep collection and analysis effort proportional to the command problem.\n"
            "- End with estimate implications, caveats, and decision support instead of generic area background.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_0202_REFERENCES),
            structured_citations=structured_citations(MOS_0202_REFERENCES),
            source_trust=source_trust_markers(
                MOS_0202_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-2 intelligence and estimate-support picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What commander decision is this intelligence effort supposed to support?",
                "What gap or assumption is still doing too much work in the estimate?",
                "What part of the problem needs collection discipline instead of more background summary?",
                "What still belongs to the broader S-2 lane rather than the 0202 officer slice?",
            ],
        )


def build_mos_intel_0202_agent() -> MosIntel0202AdvisorAgent:
    return MosIntel0202AdvisorAgent()
