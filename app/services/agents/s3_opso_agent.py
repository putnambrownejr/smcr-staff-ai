from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import Agent, AgentContext


class S3OpsOAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s3-opso",
            name="S-3 / OpsO Advisor",
            description=(
                "Supports battalion or higher S-3/OpsO style reserve operations planning, training synchronization, "
                "battle rhythm, and staff-product discipline."
            ),
            domain="operations and training",
            intended_users=["SMCR officers", "OpsO", "S-3", "Chief of Staff / Aide", "command teams"],
            allowed_sources=[
                "public doctrine and planning references",
                "public training and readiness references",
                "public ORM and safety references",
                "local handoff, action, and planning summaries",
            ],
            disallowed_inputs=[
                "classified operations",
                "exact real-world movement details",
                "sensitive plans in unapproved environments",
                "private rosters and readiness data beyond minimum need",
            ],
            system_prompt=(
                "Respond like a practical reserve S-3/OpsO. Focus on synchronization, mission analysis, battle rhythm, "
                "training value, and decision support. Stay advisory and require human review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-3 / OpsO advisory draft.\n\n"
            "Use this to shape reserve operations and training planning, not as authoritative command guidance.\n\n"
            "Primary S-3 lenses:\n"
            "- What is the mission or training objective, and what decision is required next?\n"
            "- What must happen this drill, before the next drill, and at the event itself?\n"
            "- Which products, rehearsals, or coordination points are on the critical path?\n"
            "- What breaks first in an SMCR context with limited drill time, distributed Marines,\n"
            "  and support dependencies?\n\n"
            "Recommended S-3 rhythm:\n"
            "- Clarify mission, commander intent, and training audience.\n"
            "- Build a short synchronization matrix across S-1, S-4, S-6, safety, and key leaders.\n"
            "- Identify products required: WARNO, task list, comm checks, risk controls, AAR plan.\n"
            "- Confirm decision points and who owns each suspense before leaving drill.\n\n"
            "Checklist:\n"
            "- Write the desired end state in plain language.\n"
            "- Identify assumptions, constraints, and missing information.\n"
            "- Separate admin due-outs from actual operational decision points.\n"
            "- Capture follow-up actions with owners and suspense dates.\n"
            "- Treat this as a training/support draft until reviewed by the command team.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "Marine Corps planning doctrine",
                "Training and readiness references",
                "ORM / safety references",
            ],
            structured_citations=[
                StructuredCitation(
                    title="Marine Corps planning doctrine",
                    confidence=Confidence.low,
                    notes="Verify current public planning doctrine before relying on this draft.",
                ),
                StructuredCitation(
                    title="Training and readiness references",
                    confidence=Confidence.low,
                    notes="Check current training/readiness references for mission-specific standards.",
                ),
                StructuredCitation(
                    title="ORM / safety references",
                    confidence=Confidence.low,
                    notes="Confirm current ORM and safety requirements before execution.",
                ),
            ],
            source_trust=[
                SourceTrustMarker(
                    tracked_title="Marine Corps planning doctrine",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Review the latest verified planning reference before finalizing staff products.",
                ),
                SourceTrustMarker(
                    tracked_title="Training and readiness references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Check current training standards before treating a plan as final.",
                ),
                SourceTrustMarker(
                    tracked_title="ORM / safety references",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current safety and ORM guidance before execution.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a drill-weekend planning problem, an AT problem, or a training-event problem?",
                "What products or decisions need to be complete by the end of this drill?",
                "Which staff sections must be synchronized for this to work in an SMCR timeline?",
            ],
        )


def build_s3_opso_agent() -> S3OpsOAdvisorAgent:
    return S3OpsOAdvisorAgent()
