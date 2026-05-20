from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_0102_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosAdjutant0102AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-adjutant-0102",
            name="MOS 0102 / Adjutant Advisor",
            description=(
                "Supports the S-1 lane with MOS-aware 0102 adjutant and manpower-officer advisory help for "
                "administration, correspondence, accountability, staffing, and reserve continuity."
            ),
            domain="administration support",
            intended_users=["Adjutants", "S-1 officers", "manpower officers", "SMCR officers"],
            allowed_sources=[
                "public manpower and administration training references",
                "public correspondence guidance",
                "public reserve administration guidance",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "SSNs",
                "PII",
                "full service records",
                "sensitive personnel actions in unapproved environments",
                "raw casualty case details",
            ],
            system_prompt=(
                "Respond like a reserve 0102 officer working in the S-1/adjutant lane. Act like the narrower MOS "
                "execution slice under the broader S-1 picture. Focus on command correspondence, accountability, "
                "awards, files, staffing discipline, and what must stay under control between drills."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 0102 adjutant advisory draft under the S-1 lane.\n\n"
            "Use this to shape administration, command correspondence, and manpower continuity, not as "
            "authoritative personnel direction.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-1 owns the broad manpower, personnel-service, admin, and travel-admin picture.\n"
            "- The 0102 adjutant lane owns the narrower officer judgment around accountability, command files, "
            "routing discipline, correspondence, awards, and keeping the command's administrative spine alive.\n\n"
            "What the MOS lane should add beyond the broad S-1 picture:\n"
            "- whether the adjutant systems are actually under control instead of just claimed on a tracker\n"
            "- whether files, directives, awards, and accountability can survive a gap between drills\n"
            "- whether correspondence and staffing actions are being routed cleanly enough to brief the XO\n"
            "- whether the unit can answer simple admin questions without a scavenger hunt\n\n"
            "My read:\n"
            "- Thin-bench S-1 shops usually fail at ownership, stale files, and nobody closing the loop on the last "
            "routing touch.\n"
            "- If the command correspondence, accountability picture, and awards lane are all living in different "
            "notebooks, the adjutant fight is already lost.\n"
            "- The reserve version of this MOS is mostly continuity discipline disguised as admin work.\n\n"
            "0102 checklist:\n"
            "- Keep one clear ownership picture for correspondence, awards, files, casualty admin, and reporting.\n"
            "- Separate what must be corrected now from what only needs continuity tracking to next drill.\n"
            "- Make routing chains, suspense dates, and final-review authority explicit.\n"
            "- Treat accountability and records accuracy as readiness issues, not clerical cleanup.\n"
            "- End with command decisions, due-outs, and missing references instead of generic admin optimism.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_0102_REFERENCES),
            structured_citations=structured_citations(MOS_0102_REFERENCES),
            source_trust=source_trust_markers(
                MOS_0102_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-1 manpower and administration picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this mainly an accountability, correspondence, awards, or staffing-control problem?",
                "What part of the S-1 picture is drifting because nobody owns it between drills?",
                "What reference, file set, or suspense owner is currently unclear?",
                "What still belongs in the broad S-1 lane rather than the 0102 adjutant slice?",
            ],
        )


def build_mos_adjutant_0102_agent() -> MosAdjutant0102AdvisorAgent:
    return MosAdjutant0102AdvisorAgent()
