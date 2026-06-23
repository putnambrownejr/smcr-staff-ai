from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MEDICAL_REFERENCES,
    S4_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class LceAgent(Agent):
    def __init__(self) -> None:
        refs = S4_REFERENCES + MEDICAL_REFERENCES + STAFF_PRODUCT_REFERENCES
        self.metadata = AgentMetadata(
            id="lce",
            name="LCE / Logistics Combat Element",
            description=(
                "MAGTF Logistics Combat Element representative — sustainment, distribution, health services, "
                "recovery and reconstitution, and LCE integration with GCE and ACE."
            ),
            domain="logistics combat element",
            intended_users=["SMCR officers", "S-4", "LCE planners", "MLG staff", "CSS planners"],
            allowed_sources=[
                "public logistics and sustainment doctrine",
                "public health services references",
                "training-only logistics scenarios",
            ],
            disallowed_inputs=[
                "classified logistics plans",
                "real-world supply request data",
                "sensitive ammunition allocation data",
                "live patient or casualty data",
            ],
            system_prompt=(
                "Respond like an LCE representative advising the MAGTF CE. Focus on sustainment integration, "
                "distribution discipline, and health services coordination. Stay training-safe and advisory."
            ),
        )
        self._refs = refs

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"

        answer = (
            "LCE / Logistics Combat Element advisory draft.\n\n"
            "Use this to shape sustainment planning and LCE integration, "
            "not to replace qualified logistics planners, local SOPs, or formal sustainment estimates.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- If sustainment, distribution, and health services are briefed as separate stories, "
            "the LCE integration value is lost.\n"
            "- The LCE exists to sustain the fight, not to run a supply warehouse.\n\n"
            "Primary LCE lenses:\n"
            "- What sustainment assumption is carrying too much weight?\n"
            "- What distribution or health-service gap surfaces first under friction?\n"
            "- What recovery/reconstitution timeline is unrealistic?\n"
            "- How does the LCE synchronize with GCE and ACE needs?\n"
            "- What logistics decision belongs to the MAGTF commander rather than the LCE?\n\n"
            "What this lane is good for:\n"
            "- LCE estimate development and sustainment support matrix\n"
            "- Distribution and health services planning within the MAGTF\n"
            "- Recovery and reconstitution planning\n"
            "- CSS coordination with GCE and ACE elements\n"
            "- Reserve logistics unit training event design\n\n"
            "Checklist:\n"
            "- Build the LCE estimate, sustainment support matrix, and recovery checklist.\n"
            "- Identify CSS coordination points with GCE and ACE.\n"
            "- Plan distribution routes, health service support, and maintenance priorities.\n"
            "- Rehearse sustainment coordination at the MAGTF level.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(
                self._refs,
                notes_prefix="Verify current logistics doctrine and local sustainment directives.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What sustainment assumption is carrying the most weight?",
                "What distribution or health-service gap surfaces first?",
                "How does the LCE synchronize with GCE and ACE needs?",
                "What recovery/reconstitution timeline is realistic?",
            ],
        )


def build_lce_agent() -> LceAgent:
    return LceAgent()
