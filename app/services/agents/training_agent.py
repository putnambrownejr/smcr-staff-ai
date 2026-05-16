from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    TRAINING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class TrainingPlannerAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="training-planner",
            name="Training Planner Agent",
            description="Builds advisory training planning guidance, event framing, and readiness prompts.",
            domain="training",
            intended_users=["TrainingO", "company staff", "battalion staff"],
            allowed_sources=["public T&R references", "public doctrine", "training-only scenarios"],
            disallowed_inputs=["private readiness rosters", "PII", "classified event details"],
            system_prompt=(
                "Respond like a practical Marine training planner. Focus on event purpose, standards, rehearsal, "
                "assessment, and what must be prepared before the next drill. Stay advisory and source-aware."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Training planner advisory draft.\n\n"
            "Use this to shape a training event, not to replace command approval or current training guidance.\n\n"
            "Primary training lenses:\n"
            "- What standard or MET/METL value is this event supposed to sharpen?\n"
            "- What must be prepared, rehearsed, and assessed before the event becomes worth the time?\n"
            "- What can be trained well this drill, and what should wait for a better-supported window?\n\n"
            "My read:\n"
            "- If the event cannot be assessed, it is usually just activity.\n"
            "- If the prerequisites are unclear, the event will turn into improvisation instead of learning.\n"
            "- Training value comes from a clear task, a realistic condition, and a disciplined AAR.\n\n"
            "Checklist:\n"
            "- Name the objective and tie it to a standard or MET/METL lane.\n"
            "- Identify prerequisites, support dependencies, and rehearsal points.\n"
            "- Keep the event simple enough to prepare honestly and assess cleanly.\n"
            "- Decide what products are required: schedule, eval plan, risk controls, and AAR capture.\n"
            "- Assign owners and suspense dates before Marines leave the drill floor.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(TRAINING_REFERENCES),
            structured_citations=structured_citations(TRAINING_REFERENCES),
            source_trust=source_trust_markers(
                TRAINING_REFERENCES,
                notes_prefix="Verify current unit training management and readiness references before execution.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What event or training objective is driving this request?",
                "Which MET, METL, or common-skill standard should anchor the event?",
                "What is the first prerequisite or support dependency likely to break the timeline?",
            ],
        )


def build_training_agent() -> TrainingPlannerAgent:
    return TrainingPlannerAgent()
