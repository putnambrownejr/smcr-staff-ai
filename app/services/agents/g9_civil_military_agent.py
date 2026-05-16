from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    G9_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class G9CivilMilitaryAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="g9-civil-military",
            name="G-9 / Civil-Military Advisor",
            description=(
                "Supports civil-military planning, partner coordination, civil information framing, and "
                "continuity for external engagement in reserve staff contexts. Includes MOS civil-affairs "
                "work as a subordinate lane for civil reconnaissance and engagement logic."
            ),
            domain="civil-military operations",
            intended_users=["SMCR officers", "G-9", "civil affairs officers", "S-3", "Chief of Staff / Aide"],
            allowed_sources=[
                "public civil affairs or civil-military doctrine",
                "public population or partner context sources",
                "public interagency or NGO references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified civil assessments",
                "private personal data",
                "sensitive partner details in unapproved environments",
                "operationally sensitive engagement plans",
            ],
            system_prompt=(
                "Respond like a practical reserve G-9 or civil-military planner. Focus on partner coordination, "
                "civil considerations, continuity, and information gaps. Stay advisory and require human review. "
                "Only show up when the civil picture actually matters."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"
        answer = (
            "G-9 / civil-military advisory draft.\n\n"
            "Use this to shape civil-military planning and partner coordination, not as authoritative engagement "
            "guidance.\n\n"
            f"{active_context_block}"
            "Primary G-9 lenses:\n"
            "- What civil or partner context matters to the command problem right now?\n"
            "- Which external relationships need deliberate coordination, and who owns that follow-up?\n"
            "- What assumptions about local familiarity, continuity, or partner access are quietly driving risk?\n"
            "- Which concerns belong in the broad G-9 lane versus the narrower civil-affairs MOS lane?\n"
            "- What information should be preserved between drills so the team does not restart from zero?\n\n"
            "My read:\n"
            "- Civil context helps only when it changes a real command problem.\n"
            "- External coordination falls apart when continuity is treated like a courtesy\n"
            "  instead of a requirement.\n\n"
            "Checklist:\n"
            "- Frame the supported problem and the civil considerations that could change it.\n"
            "- Separate stakeholders, partner types, and engagement objectives clearly.\n"
            "- Keep population/context research public, attributable, and caveated.\n"
            "- Capture continuity notes, next actions, and revalidation points before drill ends.\n"
            "- Keep outputs in the checklist and coordination lane, not as authoritative tasking.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(G9_REFERENCES),
            structured_citations=structured_citations(G9_REFERENCES),
            source_trust=source_trust_markers(
                G9_REFERENCES,
                notes_prefix="Verify current civil-affairs and civil-military references before action.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What supported command problem or event is driving this G-9 request?",
                "Which partner set matters most here: local authorities, interagency, NGO, or community leaders?",
                "What continuity note should survive to the next drill period?",
            ],
        )


def build_g9_civil_military_agent() -> G9CivilMilitaryAdvisorAgent:
    return G9CivilMilitaryAdvisorAgent()
