from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    SEL_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class SelEnlistedLeaderAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="sel-enlisted-leader",
            name="SEL / SgtMaj / 1stSgt Advisor",
            description=(
                "Supports command-team enlisted leadership judgment around ceremony, process, standards, customs, "
                "courtesies, accountability, formations, and USMC institutional procedure."
            ),
            domain="senior enlisted leadership",
            intended_users=["SMCR officers", "SgtMaj", "1stSgt", "XO", "OIC", "command teams"],
            allowed_sources=[
                "public drill and ceremonies references",
                "public Marine Corps manual references",
                "public uniform and common-skills references",
                "public correspondence and protocol references",
                "local planning summaries",
            ],
            disallowed_inputs=[
                "classified event details",
                "private disciplinary matters beyond minimum advisory framing",
                "sensitive personal data",
                "official command authority impersonation",
            ],
            system_prompt=(
                "Respond like a seasoned Marine Corps senior enlisted leader. Focus on standards, ceremony, customs, "
                "courtesies, formations, process, accountability, and what will embarrass the unit if ignored. Stay "
                "practical, direct, advisory, and grounded in official public references."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "SEL / SgtMaj / 1stSgt advisory draft.\n\n"
            "Use this to shape command-team enlisted judgment, not to replace command authority or local SOP.\n\n"
            "Bottom line:\n"
            "- Ceremonies and formal processes are standards events, not improvisation events.\n"
            "- If nobody owns sequence, participants, timing, dress, and accountability,\n"
            "  the unit will look confused.\n\n"
            "Primary SEL lenses:\n"
            "- What standard, custom, or formal process actually governs this event?\n"
            "- Who is responsible for sequence control, accountability, uniform, and rehearsal?\n"
            "- What part of this plan will make the unit look unprepared if it goes unverified?\n"
            "- What belongs in command guidance, and what belongs in a checklist or rehearsal script?\n\n"
            "My read:\n"
            "- Marines forgive complexity faster than they forgive sloppiness in standards.\n"
            "- The first failure is usually not motivation;\n"
            "  it is unclear sequence, weak rehearsal, or casual assumptions.\n"
            "- If this is a ceremony, formation, or formal evolution,\n"
            "  the timeline and responsibilities need to be explicit.\n\n"
            "Checklist:\n"
            "- Identify the governing standard or reference before writing the event flow.\n"
            "- Name the OIC/SNCOIC, sequence controller, and accountability owner.\n"
            "- Confirm uniform, reporting time, formation sequence, and command relationship.\n"
            "- Rehearse transitions, movements, honors, speaking order, and release criteria.\n"
            "- Separate what is mandatory by standard from what is local flavor.\n"
            "- Treat unresolved protocol or ceremony questions as issues to verify before execution.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(SEL_REFERENCES),
            structured_citations=structured_citations(SEL_REFERENCES),
            source_trust=source_trust_markers(
                SEL_REFERENCES,
                notes_prefix="Verify current ceremony, standards, and protocol references before execution.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a ceremony, formation, formal visit, relief, retirement, or general standards issue?",
                "Who owns sequence control, accountability, and rehearsal?",
                "What official reference or local SOP is already in hand?",
            ],
        )


def build_sel_enlisted_leader_agent() -> SelEnlistedLeaderAdvisorAgent:
    return SelEnlistedLeaderAdvisorAgent()
