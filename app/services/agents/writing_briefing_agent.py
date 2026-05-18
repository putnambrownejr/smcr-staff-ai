from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    WRITING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class WritingBriefingCoachAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="writing-briefing-coach",
            name="Writing / Briefing Coach",
            description=(
                "Sharpens staff writing and briefing quality by focusing on audience, decision, structure, evidence, "
                "and brevity."
            ),
            domain="communication",
            intended_users=["SMCR officers", "staff officers", "XO", "command teams"],
            allowed_sources=[
                "public correspondence guidance",
                "public command and staff PME references",
                "local training-only staff products",
            ],
            disallowed_inputs=[
                "classified or sensitive official products in unapproved environments",
            ],
            system_prompt=(
                "Respond like a command-and-staff writing coach. Help the user produce cleaner briefs and products "
                "without smothering them in academic language."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Writing / briefing coach advisory.\n\n"
            "Use this when the product exists but the thinking is getting lost in the prose.\n\n"
            "Pressure these questions:\n"
            "- Who is the audience?\n"
            "- What decision or understanding is required?\n"
            "- What belongs in the main body, and what belongs in backup?\n"
            "- What claim needs evidence or a source note?\n"
            "- What can be cut without losing the point?\n\n"
            "Good staff-product habits:\n"
            "- Lead with the problem, decision, or recommendation.\n"
            "- Use headings that reflect thought, not paperwork.\n"
            "- Keep each paragraph doing one job.\n"
            "- Make assumptions and caveats explicit instead of hiding them in tone.\n"
            "- Build slides and briefs around what the commander must grasp quickly.\n"
            "- If the product is clean but the logic is weak, fix the logic first.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(WRITING_REFERENCES),
            structured_citations=structured_citations(WRITING_REFERENCES),
            source_trust=source_trust_markers(
                WRITING_REFERENCES,
                notes_prefix="Verify current correspondence and PME references before formal use.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Who is the audience for this product or brief?",
                "What decision or understanding should the audience leave with?",
                "What part belongs in backup instead of the main product?",
            ],
        )


def build_writing_briefing_agent() -> WritingBriefingCoachAgent:
    return WritingBriefingCoachAgent()
