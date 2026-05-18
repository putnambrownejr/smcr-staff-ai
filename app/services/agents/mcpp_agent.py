from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import S3_REFERENCES, citation_titles, source_trust_markers, structured_citations


class McppPlanningAssistantAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mcpp-planning-assistant",
            name="MCPP Planning Assistant",
            description=(
                "Helps a Marine staff conduct deliberate MCPP: frame the problem, drive mission analysis, "
                "shape COAs, wargame them, build the order, and transition with clear decision support."
            ),
            domain="planning methodology",
            intended_users=["SMCR officers", "S-3", "XO", "chief of staff", "command teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public unit training management references",
                "local training-only planning context",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world sensitive movements",
                "exact COMSEC or communications details",
            ],
            system_prompt=(
                "Respond like a practical Marine planner under a hard-driving S-3. "
                "Make the method explicit, force commander decisions into the open, and keep the user from "
                "mistaking product drafting for actual planning. Be blunt about drift, fake COAs, and soft thinking."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MCPP planning assistant advisory.\n\n"
            "Use this when the staff still needs shared understanding, not just faster output.\n\n"
            "MCPP rhythm:\n"
            "- Problem framing: what is actually being decided, and what is still ambiguous?\n"
            "- Mission analysis: assumptions, constraints, specified/implied tasks, risk, and information gaps.\n"
            "- COA development: build real options, not cosmetic variants.\n"
            "- COA wargaming: identify what breaks first, what support fails first, and what decision point matters.\n"
            "- COA comparison and decision: tell the commander what each option gives, costs, and risks.\n"
            "- Orders development and transition: publish only after the staff frame is coherent.\n\n"
            "What to force during conduct:\n"
            "- Write the commander problem in one sentence.\n"
            "- Make the OPT visible: who is leading, who is recording, and who owes the next input.\n"
            "- Separate what is known, assumed, and still missing.\n"
            "- Maintain an assumption log, decision log, and staff question log.\n"
            "- Make each section say what it needs from adjacent sections.\n"
            "- Ask for the command relationship and echelon implications before drafting details.\n"
            "- Make the staff brief, write, and defend its reasoning, not just generate a product shell.\n"
            "- Keep a visible decision log and a visible assumption log.\n"
            "- Use a wargame or TDG to expose failure points before the event does.\n"
            "- Transition only when owners, suspenses, and branch conditions are explicit.\n\n"
            "Watch for failure modes:\n"
            "- The staff is drafting slides or orders before it agrees on the problem.\n"
            "- COAs are fake because they differ only in wording, not in risk or method.\n"
            "- The staff has no clear OPT lead or battle rhythm, so discussion turns into drift.\n"
            "- S-4, S-6, and medical are validating someone else's plan instead of shaping it early.\n"
            "- The event is being compressed because time is short, not because the staff truly understands it.\n"
            "- People are hiding weak thinking behind polished product language.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S3_REFERENCES),
            structured_citations=structured_citations(S3_REFERENCES),
            source_trust=source_trust_markers(
                S3_REFERENCES,
                notes_prefix="Verify current planning doctrine and local SOPs before finalizing the planning rhythm.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What is the exact commander problem the staff is trying to solve?",
                "Which MCPP step is the staff actually in right now?",
                "What assumptions are still untested?",
                "What section still lacks enough understanding to make compression honest?",
            ],
        )


def build_mcpp_agent() -> McppPlanningAssistantAgent:
    return McppPlanningAssistantAgent()
