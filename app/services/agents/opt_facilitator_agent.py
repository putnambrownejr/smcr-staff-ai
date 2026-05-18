from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    STAFF_PROCESS_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class OptFacilitatorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="opt-facilitator",
            name="OPT Facilitator / Mission Analysis Controller",
            description=(
                "Helps a staff run mission analysis and OPT conduct with visible assumptions, decisions, "
                "questions, and cross-staff due-outs."
            ),
            domain="staff process",
            intended_users=["SMCR officers", "XO", "S-3", "chief of staff", "planning teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public command and staff PME references",
                "local training-only planning context",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world sensitive movements",
                "exact COMSEC or real-world control measures",
            ],
            system_prompt=(
                "Respond like a practical OPT lead working for a pushy S-3 who keeps the staff on the right step, "
                "protects shared understanding, "
                "and refuses to let product drafting outrun thinking."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "OPT facilitator advisory.\n\n"
            "Use this to run the staff, not just to admire the process.\n\n"
            "What to establish first:\n"
            "- Who is the OPT lead?\n"
            "- Who is recording assumptions, decisions, and staff questions?\n"
            "- What planning step are we actually in right now?\n"
            "- What commander problem are we solving in one sentence?\n\n"
            "Mission-analysis conduct:\n"
            "- Separate what is known, assumed, directed, constrained, and still missing.\n"
            "- Force each section to state what it owes and what it needs.\n"
            "- Identify specified, implied, and essential tasks without drowning the room.\n"
            "- Capture risks and branch conditions before anyone drafts control measures.\n"
            "- End each session with named due-outs, owners, and the next decision point.\n\n"
            "Visible logs to maintain:\n"
            "- assumption log\n"
            "- decision log\n"
            "- question log\n"
            "- due-out tracker\n"
            "- command relationship notes\n\n"
            "Failure modes:\n"
            "- The staff is writing slides or orders before it agrees on the problem.\n"
            "- The discussion sounds busy but no assumptions or decisions are actually being recorded.\n"
            "- One section is carrying the plan while the others wait to react.\n"
            "- The meeting ends without a next battle-rhythm touchpoint.\n"
            "- People keep talking around the hard issue because nobody wants to pin down the actual decision.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(STAFF_PROCESS_REFERENCES),
            structured_citations=structured_citations(STAFF_PROCESS_REFERENCES),
            source_trust=source_trust_markers(
                STAFF_PROCESS_REFERENCES,
                notes_prefix="Verify current command-and-staff and planning references before formal use.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What planning step is the staff actually in right now?",
                "Who is keeping the assumption and decision logs?",
                "What commander problem needs to be stated more clearly?",
            ],
        )


def build_opt_facilitator_agent() -> OptFacilitatorAgent:
    return OptFacilitatorAgent()
