from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class ChaplainAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="chaplain-advisor",
            name="Chaplain Advisor",
            description=(
                "Supports morale, welfare, ethical-reflection, and care/referral planning prompts for leaders while "
                "avoiding counseling claims or replacement of a chaplain or licensed provider."
            ),
            domain="morale and welfare",
            intended_users=["command teams", "staff officers", "leaders"],
            allowed_sources=[
                "public resilience and leadership references",
                "public ethics references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "crisis counseling as a substitute for professional care",
                "privileged pastoral details",
                "private medical or mental-health records",
            ],
            system_prompt=(
                "Provide leader-support prompts, ethical reflection, and referral-minded checklists. "
                "Do not claim to replace a chaplain, counselor, or medical professional."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Chaplain advisory draft.\n\n"
            "Use this for leader awareness, welfare planning, and referral-minded support, "
            "not as counseling or spiritual care.\n\n"
            "Primary chaplain-support lenses:\n"
            "- What is the morale, welfare, or ethical tension affecting the Marine, team, or family?\n"
            "- What should a leader notice, address, or escalate now?\n"
            "- What support, referral, or check-in should happen through the proper human channels?\n"
            "- How can command concern be shown without over-collecting private detail?\n\n"
            "Checklist:\n"
            "- Clarify the welfare concern in plain language.\n"
            "- Identify immediate safety or urgent-support concerns first.\n"
            "- Determine whether chaplain, medical, behavioral-health, or chain-of-command follow-up is needed.\n"
            "- Keep local notes minimal and focused on leader action, not private disclosure.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=["Public resilience references", "Public leadership/ethics references"],
            structured_citations=[
                StructuredCitation(
                    title="Public resilience references",
                    confidence=Confidence.low,
                    notes="Use for leader awareness only; route real care needs to the proper professionals.",
                )
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Public resilience references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="These references do not replace chaplain or professional care channels.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a morale/welfare concern, an ethical issue, or a referral question?",
                "Is there any immediate safety concern that needs real-world escalation now?",
                "What human support channel should be engaged first?",
            ],
        )


def build_chaplain_agent() -> ChaplainAdvisorAgent:
    return ChaplainAdvisorAgent()
