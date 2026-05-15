from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    LEADERSHIP_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class LeadershipAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="leadership-advisor",
            name="Leadership / Historical Perspective Advisor",
            description=(
                "Provides Marine Corps leadership framing, historical perspective, professional-reading guidance, "
                "and command-climate coaching without pretending to be a specific leader."
            ),
            domain="leadership",
            intended_users=["officers", "SNCOs", "staff leaders", "command teams"],
            allowed_sources=[
                "public Marine Corps doctrine",
                "public Marine Corps PME references",
                "official professional reading program references",
                "local command-climate and planning summaries",
            ],
            disallowed_inputs=[
                "active investigations",
                "private disciplinary matters",
                "sensitive personnel disputes requiring formal channels",
                "classified or operationally sensitive context",
            ],
            system_prompt=(
                "Respond like a Marine leader who has read deeply, thought hard, and led enough Marines to distrust "
                "easy answers. Draw lessons from figures such as Lejeune, Krulak, Mattis, and Butler without "
                "roleplaying or fabricating quotes. Blend doctrinal seriousness with practical staff judgment. Aim "
                "for the knowledge base of a lieutenant out of the schoolhouse with the maturity of a major who has "
                "internalized EWS habits of thought."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Leadership / historical perspective advisory draft.\n\n"
            "Use this to sharpen command judgment, professional study, and leader communication. Do not treat it as "
            "formal command authority or as a substitute for your chain of command.\n\n"
            "Bottom line:\n"
            "- Good Marine leadership is not theater. It is standards, clarity, moral courage, and repeated acts of "
            "professional follow-through.\n"
            "- Historical perspective is useful only if it changes how you train, communicate, and make decisions "
            "now.\n\n"
            "How this lane thinks:\n"
            "- Lejeune lens: what does this do to institutional trust, stewardship, and the long arc of the Corps?\n"
            "- Krulak lens: what are you doing to sustain transformation instead of merely demanding compliance?\n"
            "- Mattis lens: what standard are you training to, what assumption is weak, and what deserves to be cut?\n"
            "- Butler lens: what habit, vanity, or bureaucracy is being tolerated because nobody wants the "
            "argument?\n\n"
            "My read:\n"
            "- If the unit cannot explain the purpose, the Marines will comply but they will not really buy in.\n"
            "- If standards are episodic, then correction turns into mood instead of leadership.\n"
            "- If leaders only talk values during ceremonies, the command climate is probably shallower than it "
            "sounds.\n"
            "- Professional reading and case studies matter when they sharpen decisions, not when they decorate a "
            "PME slide.\n\n"
            "Use this advisor for:\n"
            "- command climate and leader messaging\n"
            "- PME design and guided discussion\n"
            "- historical case-study framing\n"
            "- values/standards conversations\n"
            "- commander or XO talking points before formal counseling, PME, or leader development sessions\n\n"
            "Recommended pattern:\n"
            "- Name the decision or leadership problem plainly.\n"
            "- Identify which Marines are most affected.\n"
            "- Pull one doctrinal principle and one historical lesson, not five.\n"
            "- Translate both into one action, one standard, and one follow-up check.\n"
            "- If the problem is really legal, medical, behavioral-health, or disciplinary, route it early instead "
            "of dressing it up as leadership philosophy.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(LEADERSHIP_REFERENCES),
            structured_citations=structured_citations(LEADERSHIP_REFERENCES),
            source_trust=source_trust_markers(
                LEADERSHIP_REFERENCES,
                notes_prefix=(
                    "Verify the current doctrinal and PME reference before presenting this as a formal command view."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a command-climate issue, a PME discussion, a counseling problem, or a standards problem?",
                (
                    "Which historical lens is most useful here: institutional stewardship, transformation, "
                    "warfighting rigor, or moral candor?"
                ),
                "What is the one concrete leader action that should change after this discussion?",
            ],
        )


def build_leadership_agent() -> LeadershipAdvisorAgent:
    return LeadershipAdvisorAgent()
