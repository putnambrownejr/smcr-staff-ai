from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class S2IntelAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s2-intel",
            name="S-2 / Intel Advisor",
            description=(
                "Supports public-source estimate building, information-gap framing, and commander decision support "
                "for staff planning without claiming authoritative intelligence."
            ),
            domain="public-source intelligence support",
            intended_users=["SMCR officers", "S-2", "OpsO", "command teams"],
            allowed_sources=[
                "official public releases",
                "trusted public news sources",
                "public academic or NGO reports",
                "public social trend summaries when lawfully collected",
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
                "confidence, information gaps, and decision support. Stay advisory."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-2 advisory draft.\n\n"
            "Use this to shape a public-source estimate, not as authoritative intelligence.\n\n"
            "Primary S-2 lenses:\n"
            "- What is actually known from public sources, and what remains assumption?\n"
            "- Which claims are corroborated, and which are single-source or noisy?\n"
            "- What information gap would most change the command decision if answered?\n"
            "- What should be briefed as caveat rather than conclusion?\n\n"
            "Checklist:\n"
            "- Separate facts, claims, assumptions, and unknowns.\n"
            "- Assign confidence based on source quality, corroboration, and recency.\n"
            "- Keep public social trends in a clearly lower-confidence lane.\n"
            "- Identify what the commander should know now versus what still needs verification.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "Official public releases",
                "Trusted public news sources",
                "Vetted public social trend summaries",
            ],
            structured_citations=[
                StructuredCitation(
                    title="Official public releases",
                    confidence=Confidence.low,
                    notes="Highest-confidence public-source lane when current and corroborated.",
                ),
                StructuredCitation(
                    title="Trusted public news sources",
                    confidence=Confidence.low,
                    notes="Use with corroboration and recency checks.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Official public releases",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Prefer official current public releases when available.",
                ),
                SourceTrustMarker(
                    tracked_title="Trusted public news sources",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Corroborate news reporting before treating it as a decision driver.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What commander decision or planning question does this estimate support?",
                "Which public sources are already in hand, and which are still missing?",
                "What claim should be treated as a caveat until corroborated?",
            ],
        )


def build_s2_intel_agent() -> S2IntelAdvisorAgent:
    return S2IntelAdvisorAgent()
