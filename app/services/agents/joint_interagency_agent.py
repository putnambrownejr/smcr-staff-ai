from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    JOINT_FRAME_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class JointInteragencyFrameAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="joint-interagency-frame-advisor",
            name="Joint / Interagency Frame Advisor",
            description=(
                "Helps the staff think beyond the Marine-only frame when command relationships, external actors, "
                "or broader operating context matter."
            ),
            domain="external coordination",
            intended_users=["SMCR officers", "field-grade staff", "XO", "G-3/G-5/G-9"],
            allowed_sources=[
                "public command and staff PME references",
                "public Marine Corps staff doctrine",
                "local training-only planning context",
            ],
            disallowed_inputs=[
                "classified interagency details",
                "sensitive operational coordination details",
            ],
            system_prompt=(
                "Respond like a practical staff officer who can widen the frame without drifting into vague theory. "
                "Focus on command relationships, external stakeholders, and why they matter to planning."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Joint / interagency frame advisory.\n\n"
            "Use this when the Marine-only frame is too narrow for the problem.\n\n"
            "What to identify:\n"
            "- Who is supported and who is supporting?\n"
            "- Which external organization actually changes the problem or the timeline?\n"
            "- What coordination must happen early rather than at the end?\n"
            "- What assumption about authorities, roles, or culture is still too casual?\n\n"
            "Good staff habits here:\n"
            "- Name the command relationship in plain language.\n"
            "- Distinguish information requirements from coordination requirements.\n"
            "- Capture what the outside actor needs from you and what you need from them.\n"
            "- Keep the external picture tied to a real decision or planning consequence.\n"
            "- Do not widen the frame just to sound smarter.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(JOINT_FRAME_REFERENCES),
            structured_citations=structured_citations(JOINT_FRAME_REFERENCES),
            source_trust=source_trust_markers(
                JOINT_FRAME_REFERENCES,
                notes_prefix="Verify current command-and-staff PME and doctrine before formal coordination.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What command relationship matters most here?",
                "Which external actor actually changes the plan or timeline?",
                "What coordination assumption still needs to be checked?",
            ],
        )


def build_joint_interagency_agent() -> JointInteragencyFrameAgent:
    return JointInteragencyFrameAgent()
