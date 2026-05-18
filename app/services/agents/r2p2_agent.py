from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S3_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class R2P2PlanningAssistantAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="r2p2-planning-assistant",
            name="R2P2 Planning Assistant",
            description=(
                "Helps a Marine staff use compressed R2P2-style planning honestly when the mission is familiar, "
                "SOP-backed, and time is the main constraint."
            ),
            domain="rapid planning methodology",
            intended_users=["SMCR officers", "S-3", "XO", "chief of staff", "command teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public training-management references",
                "local training-only planning context",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world sensitive movements",
                "exact COMSEC or communications details",
            ],
            system_prompt=(
                "Respond like a Marine planner protecting the integrity of compressed planning. "
                "Only recommend R2P2 when the staff already understands the problem and has SOPs, "
                "baseline products, and rehearsal habits to support real compression."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "R2P2 planning assistant advisory.\n\n"
            "Use this only when the problem is already familiar enough that time, not understanding, "
            "is the real constraint.\n\n"
            "Before using compressed planning, confirm:\n"
            "- The unit has baseline SOPs, templates, and command relationships already understood.\n"
            "- The staff can state the mission, main constraints, and likely branch conditions without "
            "re-learning the problem.\n"
            "- The commander problem is narrow enough to refine quickly.\n"
            "- The staff is updating a known concept, not discovering a new one.\n\n"
            "Compressed conduct rhythm:\n"
            "- Reconfirm the mission and decision in plain language.\n"
            "- Identify only what changed.\n"
            "- Validate the assumptions most likely to break the concept.\n"
            "- Run a short branch/sequel drill or TDG.\n"
            "- Publish only the changed tasks, changed support, changed control measures, and changed suspenses.\n"
            "- Push unresolved friction into named actions immediately.\n\n"
            "Abort compressed planning and return to deliberate MCPP if:\n"
            "- The staff cannot agree on the problem.\n"
            "- Support, medical, comm, or subordinate relationships are still unclear.\n"
            "- The concept depends on assumptions nobody has actually checked.\n"
            "- The staff is using the word 'rapid' to excuse confusion.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S3_REFERENCES),
            structured_citations=structured_citations(S3_REFERENCES),
            source_trust=source_trust_markers(
                S3_REFERENCES,
                notes_prefix=(
                    "Verify current doctrine and local SOP maturity before treating compression "
                    "as legitimate R2P2."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What about this problem is already familiar enough to justify compression?",
                "What SOPs or baseline products already exist?",
                "Which assumption would force you to fall back to deliberate MCPP?",
                "What exactly changed since the last known good plan?",
            ],
        )


def build_r2p2_agent() -> R2P2PlanningAssistantAgent:
    return R2P2PlanningAssistantAgent()
