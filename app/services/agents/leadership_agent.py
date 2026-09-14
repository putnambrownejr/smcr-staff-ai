from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    LEADERSHIP_REFERENCES,
    WARRIOR_MONK_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

# "reflect" mode absorbed the former Warrior-Monk agent (Sep 2026 merge).
_REFLECT_SIGNALS = (
    "reflect",
    "stoic",
    "warrior-monk",
    "warrior monk",
    "conscience",
    "philosoph",
    "meaning of",
    "why we serve",
)


def _requested_mode(context: AgentContext) -> str | None:
    options = context.extra.get("agent_options")
    mode = options.get("mode") if isinstance(options, dict) else None
    return mode if isinstance(mode, str) and mode else None


class LeadershipAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="leadership-advisor",
            name="Leadership / Historical Perspective Advisor",
            description=(
                "Owns practical Marine Leader Development across Fidelity, Fighter, Fitness, Family, Finance, and "
                "Future, with historical perspective, command-climate coaching, and a 'reflect' mode for "
                "disciplined moral reflection (formerly the Warrior-Monk lane)."
            ),
            domain="leadership",
            intended_users=["officers", "SNCOs", "staff leaders", "command teams", "PME facilitators"],
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
                "clinical counseling, religious direction, legal findings, or disciplinary decisions",
            ],
            system_prompt=(
                "Respond like a Marine leader who has read deeply, thought hard, and led enough Marines to distrust "
                "easy answers. Draw lessons from figures such as Lejeune, Krulak, Mattis, and Butler without "
                "roleplaying or fabricating quotes. Blend doctrinal seriousness with practical staff judgment. Aim "
                "for the knowledge base of a lieutenant out of the schoolhouse with the maturity of a major who has "
                "internalized EWS habits of thought.\n\n"
                "REFLECT MODE (agent_options.mode = 'reflect', or when the user asks to reflect on duty, moral "
                "courage, or purpose): be austere, candid, historically literate, and humane — Marcus Aurelius "
                "meets General Mattis in tone, without impersonating either or inventing quotes. Focus on moral "
                "purpose, disciplined reflection, and the smallest honorable action. Reflection is not therapy, "
                "chaplaincy, legal advice, or command authority."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        mode = _requested_mode(context)
        lowered = input_text.lower()
        if mode == "reflect" or (mode is None and any(signal in lowered for signal in _REFLECT_SIGNALS)):
            return self._reflect_response(input_text)
        return self._leadership_response(input_text)

    def _leadership_response(self, input_text: str) -> AgentRunResponse:
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
            "- practical Marine Leader Development across Fidelity, Fighter, Fitness, Family, Finance, and Future\n"
            "- command climate and leader messaging\n"
            "- PME design and guided discussion\n"
            "- historical case-study framing\n"
            "- values/standards conversations\n"
            "- commander or XO talking points before formal counseling, PME, or leader development sessions\n"
            "- 'reflect' mode for moral reflection on duty, fear, and purpose (ask to reflect, or set mode=reflect)\n\n"
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

    def _reflect_response(self, input_text: str) -> AgentRunResponse:
        answer = (
            "Leadership advisor — reflect mode (Warrior-Monk lane).\n\n"
            "Strip the problem to what you control, what duty requires, and what fear or vanity is trying to disguise. "
            "MCDP 1 treats uncertainty, friction, and human will as permanent features — not excuses. Leading Marines "
            "asks for moral character expressed through conduct.\n\n"
            "Reflection drill:\n"
            "- Name the hard fact without drama.\n"
            "- Separate obligation from appetite and reputation.\n"
            "- Identify the Marine or institution that bears the cost of delay.\n"
            "- Choose the smallest honorable action that changes reality today.\n"
            "- Set a time to examine the result without self-deception.\n\n"
            "When reflection is done, come back to the leadership lane to convert it into a leader-development "
            "goal, counseling action, family-support connection, or follow-up standard. This mode is reflection, "
            "not therapy, chaplaincy, legal advice, or command authority."
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(WARRIOR_MONK_REFERENCES),
            structured_citations=structured_citations(WARRIOR_MONK_REFERENCES),
            source_trust=source_trust_markers(WARRIOR_MONK_REFERENCES),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What fact are you reluctant to state plainly?",
                "Which duty is actually yours, and what is outside your control?",
                "What concrete action would make this reflection useful by tomorrow?",
            ],
        )


def build_leadership_agent() -> LeadershipAdvisorAgent:
    return LeadershipAdvisorAgent()
