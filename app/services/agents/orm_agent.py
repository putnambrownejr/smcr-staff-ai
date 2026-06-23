from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    ORM_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class OrmRiskManagementAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="orm-risk-management",
            name="ORM / Safety / Risk Management",
            description=(
                "Produces advisory risk framing, control prompts, residual-risk thinking, "
                "ORM worksheets, no-go criteria, rehearsal safety briefs, and safety officer "
                "products for training events."
            ),
            domain="safety and risk management",
            intended_users=["Safety officers", "staff officers", "leaders", "OICs", "range officers"],
            allowed_sources=[
                "public risk management doctrine",
                "training scenario inputs",
                "public safety references",
                "MCO 5100.29 (Safety Program)",
                "unit safety SOPs",
            ],
            disallowed_inputs=[
                "medical PII",
                "real mishap details requiring protected handling",
                "official risk acceptance impersonation",
            ],
            system_prompt=(
                "Prompt structured ORM and safety thinking without replacing formal safety review. "
                "Focus on hazards, controls, residual risk, supervision, no-go criteria, "
                "rehearsal safety briefs, and commander decision points."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "ORM / Safety / Risk Management advisory draft.\n\n"
            "Use this to shape risk thinking, safety products, and control development, "
            "not to replace formal safety review or risk acceptance.\n\n"
            "Primary ORM lenses:\n"
            "- What hazard actually threatens the event, and what is just background inconvenience?\n"
            "- What control must exist before execution versus what only makes the event smoother?\n"
            "- Who owns supervision, residual-risk acceptance, and stop-training authority?\n\n"
            "Safety officer products:\n"
            "- ORM worksheet: hazard identification, risk assessment, control measures, residual risk.\n"
            "- No-go criteria: conditions that stop the event before or during execution.\n"
            "- Residual-risk decision note: what risk remains after controls, who accepts it.\n"
            "- Rehearsal safety brief: safety-specific items for inclusion in rehearsals.\n"
            "- Range/event safety plan: safety overlay for field training or live-fire events.\n\n"
            "My read:\n"
            "- Weak ORM usually lists hazards without changing the plan.\n"
            "- If nobody can name the no-go criteria, then the control plan is not mature yet.\n"
            "- The right question is not whether risk exists; it is whether the unit has deliberately "
            "prepared for it.\n"
            "- Safety officer products that nobody reads are just checkbox compliance — "
            "good safety products change the plan or the brief.\n\n"
            "Checklist:\n"
            "- Identify the main hazards, likely consequences, and the controls that actually matter.\n"
            "- Separate leader verification checks from command decision points.\n"
            "- Name supervision, residual-risk owner, and stop-training triggers.\n"
            "- Develop explicit no-go criteria and rehearsal safety brief items.\n"
            "- Carry unresolved high-risk items to command review instead of hiding them in a worksheet.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(ORM_REFERENCES),
            structured_citations=structured_citations(ORM_REFERENCES),
            source_trust=source_trust_markers(
                ORM_REFERENCES,
                notes_prefix="Verify current safety references and local authority for final risk decisions.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What event, lane, or movement problem is driving the risk review?",
                "What hazard is most likely to become a no-go issue if left vague?",
                "Who is the right leader or commander to review residual risk before execution?",
            ],
        )


def build_orm_agent() -> OrmRiskManagementAgent:
    return OrmRiskManagementAgent()
