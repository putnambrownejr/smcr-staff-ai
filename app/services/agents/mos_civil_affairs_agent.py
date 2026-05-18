from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    G9_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosCivilAffairsAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-civil-affairs",
            name="MOS Civil Affairs Advisor",
            description=(
                "Supports the G-9 / civil-military lane with MOS-aware civil affairs planning, civil "
                "reconnaissance framing, and continuity-minded engagement support."
            ),
            domain="civil affairs support",
            intended_users=["Civil affairs officers", "G-9 staff", "planners", "SMCR staff"],
            allowed_sources=[
                "public civil affairs doctrine",
                "public civil-military doctrine",
                "public population or partner context sources",
                "public interagency or NGO references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified assessments",
                "targeting",
                "private personal data",
                "sensitive partner details in unapproved environments",
                "operationally sensitive engagement plans",
            ],
            system_prompt=(
                "Respond like a reserve civil affairs officer working under the G-9 or civil-military lane. "
                "Act like the narrower MOS execution slice of the broader G-9 picture. Focus on civil "
                "reconnaissance, engagement logic, information handling, continuity, and public-source grounding "
                "without pretending to issue authoritative tasking."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS Civil Affairs advisory draft under the G-9 lane.\n\n"
            "Use this to shape civil affairs thinking, civil reconnaissance framing, and continuity support, "
            "not as authoritative engagement guidance.\n\n"
            "Relationship to the parent lane:\n"
            "- The G-9 owns the broad civil-military frame, external coordination picture, and command problem.\n"
            "- The MOS civil-affairs lane owns disciplined civil reconnaissance, engagement logic, continuity "
            "notes, and what is actually worth collecting.\n\n"
            "What the MOS lane should add beyond the broad G-9 picture:\n"
            "- what civil information is actually worth collecting\n"
            "- how to frame observations without drifting into trivia\n"
            "- how to preserve continuity between drill periods and handoffs\n"
            "- how to keep public-source population context useful and attributable\n\n"
            "My read:\n"
            "- Civil affairs value comes from disciplined observation tied to a command problem, not from "
            "collecting everything that sounds interesting.\n"
            "- If continuity notes die at the end of drill, the next team starts over and partner trust gets wasted.\n"
            "- Good CA work separates stakeholder, capability, need, friction, and follow-up instead of blurring "
            "them into one warm paragraph.\n\n"
            "Civil affairs checklist:\n"
            "- State the supported command problem and the civil question that actually matters.\n"
            "- Separate civil reconnaissance tasks from engagement tasks and from staff follow-up tasks.\n"
            "- Use public-source grounding for area, population, infrastructure, governance, or partner context.\n"
            "- Capture what changed, who matters, what remains unknown, and what should be revalidated next drill.\n"
            "- End with continuity notes, engagement cautions, and decision points instead of generic optimism.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(G9_REFERENCES),
            structured_citations=structured_citations(G9_REFERENCES),
            source_trust=source_trust_markers(
                G9_REFERENCES,
                notes_prefix="Use this MOS lane under the broader G-9 and civil-military planning picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What command problem is the civil picture supposed to clarify?",
                (
                    "What civil information category matters most here: governance, essential services, "
                    "population, or partner capacity?"
                ),
                "What continuity note must survive to the next drill so the unit does not restart from zero?",
                "What belongs in the broad G-9 coordination lane versus the MOS civil-affairs lane?",
            ],
        )


def build_mos_civil_affairs_agent() -> MosCivilAffairsAdvisorAgent:
    return MosCivilAffairsAdvisorAgent()
