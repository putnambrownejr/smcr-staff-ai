from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S3_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class S3OpsOAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s3-opso",
            name="S-3 / OpsO Advisor",
            description=(
                "Supports battalion or higher S-3/OpsO style reserve operations planning, training synchronization, "
                "battle rhythm, staff-product discipline, and reserve training design tied to METs, METLs, "
                "and command decision points, with a hard-edged command-training tone inspired by General Mattis's "
                "public leadership style. Includes wargaming and TDG support as an S-3 training-judgment lane."
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
                "first, force standards and purpose into the open, and stay advisory."
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
            "- What wargame, TDG, or branch-plan rehearsal would expose weak assumptions before execution?\n"
            "- What breaks first in an SMCR context with limited drill time, distributed Marines,\n"
            "  and support dependencies?\n\n"
            "My read:\n"
            "- Build around MET/METL value, not around activity for activity's sake.\n"
            "- Pick the few events the unit can actually prepare, rehearse, and assess well.\n"
            "- Demand enough realism to matter, but not so much complexity that the unit learns confusion\n"
            "  instead of competence.\n"
            "- If the event cannot survive contact with reserve timelines, the design is wrong, not the Marines.\n"
            "- Force owners and suspense dates onto every product before people leave drill.\n\n"
            "Recommended S-3 rhythm:\n"
            "- Clarify mission, commander intent, and training audience.\n"
            "- Build a short synchronization matrix across S-1, S-4, S-6, safety, and key leaders.\n"
            "- Identify products required: LOI/WARNO, task list, schedule, eval plan, comm checks, risk controls,\n"
            "  and AAR plan.\n"
            "- Use TDGs or short wargaming sessions when you need to test judgment, branch plans, or commander "
            "  decision points before execution.\n"
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
            citations=citation_titles(S3_REFERENCES),
            structured_citations=structured_citations(S3_REFERENCES),
            source_trust=source_trust_markers(
                S3_REFERENCES,
                notes_prefix="Verify current planning, training, and PME references before final event design.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a drill-weekend planning problem, an AT problem, or a training-event problem?",
                "Which MET or METL task is this event supposed to improve?",
                "What products or decisions need to be complete by the end of this drill?",
                "Would a TDG or short wargame expose the weak assumption before the event does?",
                "Which staff sections must be synchronized for this to work in an SMCR timeline?",
            ],
        )


def build_s3_opso_agent() -> S3OpsOAdvisorAgent:
    return S3OpsOAdvisorAgent()
