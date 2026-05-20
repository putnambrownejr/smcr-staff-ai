from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_3002_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosSupply3002AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-supply-3002",
            name="MOS 3002 / Supply Officer Advisor",
            description=(
                "Supports the S-4 lane with MOS-aware 3002 advisory help for accountability, fiscal discipline, "
                "supply support, and command supply readiness."
            ),
            domain="supply support",
            intended_users=["Supply officers", "S-4 staff", "command supply planners", "SMCR officers"],
            allowed_sources=[
                "public supply doctrine",
                "public supply training references",
                "public logistics professional-development references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "sensitive property serial data",
                "real fiscal account details",
                "controlled inventory specifics in unapproved environments",
                "nonpublic audit findings",
            ],
            system_prompt=(
                "Respond like a reserve 3002 working under the S-4. Act like the narrower supply-accountability "
                "slice of the broader logistics picture. Focus on property accountability, supply support, fiscal "
                "discipline, inspections, and the ugly administrative failures that quietly wreck readiness."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 3002 supply officer advisory draft under the S-4 lane.\n\n"
            "Use this to shape supply support and accountability thinking, not as authoritative fiscal or supply "
            "direction.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-4 owns the broad logistics and supportability picture.\n"
            "- The 3002 lane owns the narrower supply-accountability fight: property visibility, records accuracy, "
            "fiscal discipline, and whether the command can prove what it says it has.\n\n"
            "What the MOS lane should add beyond the broad S-4 picture:\n"
            "- a harder read on supply records, inventory readiness, and command-accountability risk\n"
            "- whether the support plan depends on gear that is on paper but not truly serviceable or visible\n"
            "- where fiscal sloppiness or certificate-of-relief problems will surface later\n"
            "- what the commander actually needs to hear about supply risk before it turns into a surprise\n\n"
            "My read:\n"
            "- 3002 value is not just requisitions. It is keeping accountability and supply support clean enough "
            "that the command does not lie to itself.\n"
            "- Reserve units often discover supply pain late because audits, inventories, and reconciliations got "
            "treated like side chores.\n"
            "- If the supply lane cannot defend its records, it cannot support the plan with confidence.\n\n"
            "3002 checklist:\n"
            "- Identify the supply support requirement, the accountability risk, and the record system that matters.\n"
            "- Separate immediate support issues from deeper inventory or fiscal-control issues.\n"
            "- Confirm whether certificates of relief, inventories, reconciliations, or fund-status reviews are "
            "in play.\n"
            "- Name what missing visibility, auditability, or fiscal control issue can degrade readiness fastest.\n"
            "- End with supply decisions, due-outs, and accountability warnings instead of a generic stock-status "
            "summary.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_3002_REFERENCES),
            structured_citations=structured_citations(MOS_3002_REFERENCES),
            source_trust=source_trust_markers(
                MOS_3002_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-4 logistics and supportability picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this mainly a supply-support issue, an accountability issue, or a fiscal-control issue?",
                "What inventory, reconciliation, or certificate-of-relief problem is least controlled right now?",
                "What command decision depends on supply data that may be less solid than advertised?",
                "What still belongs to the broader S-4 lane rather than the 3002 supply slice?",
            ],
        )


def build_mos_supply_3002_agent() -> MosSupply3002AdvisorAgent:
    return MosSupply3002AdvisorAgent()
