from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_0511_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosMagtfPlanner0511AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-magtf-planner-0511",
            name="MOS 0511 / MAGTF Planner Advisor",
            description=(
                "Supports the S-3 lane with MOS-aware 0511 advisory help for planning support, staff-product "
                "discipline, mission analysis, and MCPP execution."
            ),
            domain="planning support",
            intended_users=["MAGTF planners", "S-3 planners", "OPT members", "SMCR officers"],
            allowed_sources=[
                "public planning doctrine",
                "public MAGTF planner training references",
                "public PME planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified plans",
                "exact real-world operations orders in unapproved environments",
                "sensitive targeting or live deployment details",
            ],
            system_prompt=(
                "Respond like a reserve 0511 planner working under the S-3. Act like the narrower MAGTF-planner "
                "slice of the broader S-3 picture. Focus on mission analysis, planning support, assumptions, "
                "decision logs, staff integration, and the discipline required to make MCPP real instead of decorative."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 0511 MAGTF planner advisory draft under the S-3 lane.\n\n"
            "Use this to shape mission analysis and staff-planning support, not as authoritative operations "
            "direction.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-3 owns the broad operations picture, training plan, and command-rhythm execution.\n"
            "- The 0511 lane owns the narrower planning-engine fight: mission-analysis structure, planning support, "
            "assumption control, staff integration, and turning commander guidance into usable staff products.\n\n"
            "What the MOS lane should add beyond the broad S-3 picture:\n"
            "- whether the planning process is actually disciplined enough to trust\n"
            "- whether assumptions, tasks, and required section inputs are being captured cleanly\n"
            "- whether the OPT is producing decisions or just busy slides\n"
            "- whether the plan can survive a handoff between drills without rebuilding from zero\n\n"
            "My read:\n"
            "- Good 0511 work is less about brilliance than about keeping the staff from drifting or lying to itself.\n"
            "- If the planning support products are weak, the staff will compensate with noise and confident "
            "nonsense.\n"
            "- Reserve staffs need ruthless mission-analysis hygiene because they do not have endless repetitions "
            "to hide behind.\n\n"
            "0511 checklist:\n"
            "- Frame the problem, mission, assumptions, specified tasks, implied tasks, and essential tasks clearly.\n"
            "- Keep one visible log for assumptions, information gaps, decisions, and due-outs.\n"
            "- Force each section to state what it owes, what it needs, and what can break the plan.\n"
            "- Keep MCPP and R2P2 honest by matching method to time, familiarity, and SOP maturity.\n"
            "- End with decisions, required inputs, and next planning touchpoints instead of generic enthusiasm.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_0511_REFERENCES),
            structured_citations=structured_citations(MOS_0511_REFERENCES),
            source_trust=source_trust_markers(
                MOS_0511_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-3 planning and operations-support picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What planning step is drifting most right now: mission analysis, COA work, or staff integration?",
                "Which assumption or missing section input is still too vague to trust?",
                "Does this problem deserve full MCPP, or is there a real case for disciplined compression?",
                "What still belongs to the broader S-3 lane rather than the 0511 planner slice?",
            ],
        )


def build_mos_magtf_planner_0511_agent() -> MosMagtfPlanner0511AdvisorAgent:
    return MosMagtfPlanner0511AdvisorAgent()
