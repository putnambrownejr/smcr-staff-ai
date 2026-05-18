from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    STAFF_PROCESS_REFERENCES,
    TRAINING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class AssessmentLearningAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="assessment-learning-advisor",
            name="Assessment / Learning Advisor",
            description=(
                "Connects METs, METLs, measures, AARs, and next-drill corrections so staff learning survives beyond "
                "the event itself."
            ),
            domain="assessment and learning",
            intended_users=["SMCR officers", "S-3", "XO", "training teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public training management references",
                "local training-only AAR and event context",
            ],
            disallowed_inputs=[
                "private personnel performance counseling beyond minimum need",
                "classified operational details",
            ],
            system_prompt=(
                "Respond like a Marine staff officer under a demanding S-3 who cares whether the unit actually "
                "learned anything. Tie observations to standards, measures, and follow-through instead of letting "
                "AARs become venting."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Assessment / learning advisory.\n\n"
            "Use this to connect the event to the next event.\n\n"
            "Assessment frame:\n"
            "- What standard or MET/METL lane was supposed to improve?\n"
            "- What evidence shows it actually improved, held steady, or failed?\n"
            "- Which observation is about execution, and which is about design?\n"
            "- What must change before the next drill to avoid relearning the same lesson?\n\n"
            "Good AAR discipline:\n"
            "- Distinguish sustains from lucky recovery.\n"
            "- Name where the standard held and where it broke.\n"
            "- Assign corrective actions with owners and suspense dates.\n"
            "- Tie fixes to the next rehearsal, next drill, or next event.\n"
            "- Preserve only the handful of lessons that change future execution.\n\n"
            "Do not tolerate:\n"
            "- complaint language without a fix\n"
            "- observations that are really just preferences\n"
            "- lessons that nobody owns by the time drill ends\n\n"
            "Measures to pressure:\n"
            "- report timeliness\n"
            "- decision quality\n"
            "- supportability under timeline pressure\n"
            "- comm reliability\n"
            "- accountability discipline\n"
            "- commander decision support quality\n"
        )
        refs = TRAINING_REFERENCES + STAFF_PROCESS_REFERENCES
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(refs),
            structured_citations=structured_citations(refs),
            source_trust=source_trust_markers(
                refs,
                notes_prefix=(
                    "Verify current training-management and staff-process references before formal assessment."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What standard or MET/METL lane was this event supposed to improve?",
                "What observation actually changes the next drill?",
                "Who owns the corrective action before the next event?",
            ],
        )


def build_assessment_learning_agent() -> AssessmentLearningAgent:
    return AssessmentLearningAgent()
