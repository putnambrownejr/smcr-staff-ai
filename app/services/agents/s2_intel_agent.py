from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S2_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class S2IntelAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s2-intel",
            name="S-2 / Intel Advisor",
            description=(
                "Supports public-source estimate building, information-gap framing, and commander decision support "
                "for staff planning without claiming authoritative intelligence. Includes OSINT and public-source "
                "research as an S-2 subordinate lane."
            ),
            domain="public-source intelligence support",
            intended_users=["SMCR officers", "S-2", "OpsO", "command teams"],
            allowed_sources=[
                "official public releases",
                "trusted public news sources",
                "public academic or NGO reports",
                "public social trend summaries when lawfully collected",
                "USGS public terrain and map products",
            ],
            disallowed_inputs=[
                "classified collection",
                "non-public data",
                "targeting requests",
                "private individual tracking",
                "operational inference from sensitive movements",
            ],
            system_prompt=(
                "Respond like a cautious S-2 using only public-source material. Focus on estimate quality, "
                "confidence, information gaps, and decision support. Treat OSINT and public-source trend review as "
                "subordinate S-2 functions. Stay advisory. Sound like someone who would rather brief one hard truth "
                "and two caveats than five shaky claims."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-2 advisory draft.\n\n"
            "Use this to shape a public-source estimate, not as authoritative intelligence.\n\n"
            "Primary S-2 lenses:\n"
            "- What is actually known from public sources, and what remains assumption?\n"
            "- Which claims are corroborated, and which are single-source or noisy?\n"
            "- What OSINT or public-source trend lane is useful, and what should stay clearly caveated?\n"
            "- What information gap would most change the command decision if answered?\n"
            "- What should be briefed as caveat rather than conclusion?\n\n"
            "My read:\n"
            "- The fastest way to mislead a commander is to sound certain before the source picture is mature.\n"
            "- If the best source is still social noise or a single article,\n"
            "  brief the uncertainty instead of polishing it.\n"
            "- S-2 earns trust by killing weak assumptions early and\n"
            "  pointing the staff at the gap that matters most.\n\n"
            "Checklist:\n"
            "- Separate facts, claims, assumptions, and unknowns.\n"
            "- Assign confidence based on source quality, corroboration, and recency.\n"
            "- Tier sources explicitly: baseline reference, official current source, news/reporting, "
            "and social/noisy indicator.\n"
            "- Use the CIA World Factbook as a baseline public reference when country background\n"
            "  or infrastructure context matters.\n"
            "- Use USGS public products as a first- or second-line source when terrain, hydrography,\n"
            "  elevation, or topographic-map context matters.\n"
            "- Prefer official current sources over news framing when the two diverge.\n"
            "- Keep public social trends in a clearly lower-confidence lane.\n"
            "- Use the OSINT lane for sourced public aggregation, not private tracking or sensitive inference.\n"
            "- Identify what the commander should know now versus what still needs verification.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S2_REFERENCES),
            structured_citations=structured_citations(S2_REFERENCES),
            source_trust=source_trust_markers(
                S2_REFERENCES,
                notes_prefix="Prefer official and doctrinally grounded public sources before news or social summaries.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What commander decision or planning question does this estimate support?",
                "Which public sources are already in hand, and which are still missing?",
                (
                    "Which source belongs in the official current-source lane, and which only belongs "
                    "in news or social context?"
                ),
                "Would a dedicated OSINT-style source aggregation pass help clarify the question?",
                "What claim should be treated as a caveat until corroborated?",
            ],
        )


def build_s2_intel_agent() -> S2IntelAdvisorAgent:
    return S2IntelAdvisorAgent()
