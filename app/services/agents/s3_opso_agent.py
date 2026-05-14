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
                "battle rhythm, staff-product discipline, and reserve training design tied to METs, METLs, "
                "and command decision points, with a hard-edged command-training tone inspired by General Mattis's "
                "public leadership style."
            ),
            domain="operations and training",
            intended_users=["SMCR officers", "OpsO", "S-3", "Chief of Staff / Aide", "command teams"],
            allowed_sources=[
                "public doctrine and planning references",
                "public training and readiness references",
                "public ORM and safety references",
                "public unit training management references",
                "local handoff, action, and planning summaries",
            ],
            disallowed_inputs=[
                "classified operations",
                "exact real-world movement details",
                "sensitive plans in unapproved environments",
                "private rosters and readiness data beyond minimum need",
            ],
            system_prompt=(
                "Respond like a practical reserve S-3/OpsO with a bias for getting to a workable plan. Focus on "
                "synchronization, mission analysis, battle rhythm, MET/METL alignment, training value, and "
                "decision support. Use plain language, high standards, and a training-first tone inspired by the "
                "public leadership style associated with General Mattis. Cut weak ideas early, name what will fail "
                "first, and stay advisory."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-3 / OpsO advisory draft.\n\n"
            "Use this to shape reserve operations and training planning, not as authoritative command guidance.\n\n"
            "Bottom line:\n"
            "- Train for war, not for comfort.\n"
            "- If it does not train to a real standard, produce a needed output, or fit the drill timeline,\n"
            "  it should come off the board.\n\n"
            "Primary S-3 lenses:\n"
            "- What is the mission or training objective, and what decision is required next?\n"
            "- What must happen this drill, before the next drill, and at the event itself?\n"
            "- Which products, rehearsals, or coordination points are on the critical path?\n"
            "- What breaks first in an SMCR context with limited drill time, distributed Marines,\n"
            "  and support dependencies?\n\n"
            "My read:\n"
            "- Build around MET/METL value, not around activity for activity's sake.\n"
            "- Pick the few events the unit can actually prepare, rehearse, and assess well.\n"
            "- Demand enough realism to matter, but not so much complexity that the unit learns confusion\n"
            "  instead of competence.\n"
            "- Force owners and suspense dates onto every product before people leave drill.\n\n"
            "Recommended S-3 rhythm:\n"
            "- Clarify mission, commander intent, and training audience.\n"
            "- Build a short synchronization matrix across S-1, S-4, S-6, safety, and key leaders.\n"
            "- Identify products required: LOI/WARNO, task list, schedule, eval plan, comm checks, risk controls,\n"
            "  and AAR plan.\n"
            "- Confirm decision points and who owns each suspense before leaving drill.\n\n"
            "Checklist:\n"
            "- Write the desired training end state in plain language.\n"
            "- Tie the event to METs, METLs, or named training standards before expanding it.\n"
            "- Identify assumptions, constraints, and missing information.\n"
            "- Separate admin due-outs from actual operational decision points.\n"
            "- Keep templates with S-3 ownership: schedule, execution matrix, eval structure, and AAR skeleton.\n"
            "- Capture follow-up actions with owners and suspense dates.\n"
            "- Treat this as a training/support draft until reviewed by the command team.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "MCWP 5-10 Marine Corps Planning Process",
                "MCO 1553.3C Unit Training Management",
                "Ground and occupational field training and readiness references",
                "ORM / safety references",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCWP 5-10 Marine Corps Planning Process",
                    confidence=Confidence.low,
                    notes="Verify current public planning doctrine before relying on this draft.",
                ),
                StructuredCitation(
                    title="MCO 1553.3C Unit Training Management",
                    confidence=Confidence.low,
                    notes="Use to ground unit training design, assessment, and planning rhythm.",
                ),
                StructuredCitation(
                    title="Ground and occupational field training and readiness references",
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
                    tracked_title="MCWP 5-10 Marine Corps Planning Process",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Review the latest verified planning reference before finalizing staff products.",
                ),
                SourceTrustMarker(
                    tracked_title="MCO 1553.3C Unit Training Management",
                    status=VerifiedSourceStatus.needs_review,
                    notes="Confirm current UTM guidance before shaping the training plan.",
                ),
                SourceTrustMarker(
                    tracked_title="Ground and occupational field training and readiness references",
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
                "Which MET or METL task is this event supposed to improve?",
                "What products or decisions need to be complete by the end of this drill?",
                "Which staff sections must be synchronized for this to work in an SMCR timeline?",
            ],
        )


def build_s3_opso_agent() -> S3OpsOAdvisorAgent:
    return S3OpsOAdvisorAgent()
