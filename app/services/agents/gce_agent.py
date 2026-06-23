from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    INFANTRY_REFERENCES,
    ORM_REFERENCES,
    S3_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class GceAgent(Agent):
    def __init__(self) -> None:
        refs = S3_REFERENCES + INFANTRY_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES
        self.metadata = AgentMetadata(
            id="gce",
            name="GCE / Ground Combat Element",
            description=(
                "MAGTF Ground Combat Element representative — ground scheme of maneuver, close combat integration, "
                "fires-maneuver coordination, and GCE sustainment within the combined-arms framework."
            ),
            domain="ground combat element and maneuver",
            intended_users=["SMCR officers", "S-3", "company commanders", "GCE planners", "battalion staff"],
            allowed_sources=[
                "public ground combat and maneuver doctrine",
                "public infantry and combined-arms references",
                "training-only ground tactical scenarios",
            ],
            disallowed_inputs=[
                "classified operational plans",
                "real-world unit movements or grid coordinates",
                "sensitive force-protection details",
                "classified rules of engagement",
            ],
            system_prompt=(
                "Respond like a GCE representative advising the MAGTF CE. Focus on ground scheme of maneuver, "
                "combined-arms integration, and close combat coordination. Stay training-safe and advisory."
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
            "GCE / Ground Combat Element advisory draft.\n\n"
            "Use this to shape ground maneuver planning and combined-arms integration, "
            "not to replace qualified ground combat leaders, local SOPs, or formal tactical planning.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- The ground scheme of maneuver is the backbone of the MAGTF fight.\n"
            "- Combined-arms integration fails when fires, maneuver, air, and logistics are planned "
            "in separate rooms.\n"
            "- Training value lives in coordination discipline, not in complexity.\n\n"
            "Primary GCE lenses:\n"
            "- Does the ground scheme of maneuver support the commander's intent?\n"
            "- Are fires, obstacles, and air integrated into the ground plan or bolted on?\n"
            "- What combined-arms coordination must be rehearsed before execution?\n"
            "- What friction in movement, sustainment, or C2 will break the plan first?\n"
            "- Where are the decision points for the ground commander?\n\n"
            "What this lane is good for:\n"
            "- Ground scheme of maneuver development and refinement\n"
            "- Combined-arms rehearsal design: how fires, obstacles, air, and maneuver meet\n"
            "- GCE sustainment and movement planning within the MAGTF\n"
            "- Ground tactical decision games and wargaming support\n"
            "- Reserve infantry and ground unit training event design\n\n"
            "My read:\n"
            "- A ground plan that cannot be briefed at a rehearsal in five minutes is too complicated "
            "for the force to execute.\n"
            "- The GCE representative's job is to make fires, obstacles, air, and sustainment serve "
            "the ground scheme — not the other way around.\n"
            "- Reserve ground units that drill coordination and rehearsals between AT will get more "
            "out of their limited field time.\n\n"
            "Checklist:\n"
            "- State the ground scheme of maneuver clearly: task, purpose, and main effort.\n"
            "- Integrate fires, obstacles, and air support into the ground plan.\n"
            "- Identify decision points, branches, and sequels for the ground commander.\n"
            "- Coordinate C2, sustainment, and movement with ACE and LCE.\n"
            "- Rehearse combined-arms coordination at the ground level before execution.\n"
            "- Make safety and stop-training criteria explicit for ground events.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(
                self._refs,
                notes_prefix="Verify current ground combat doctrine and local training directives.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What is the ground scheme of maneuver and commander's intent?",
                "How are fires, obstacles, and air integrated into the ground plan?",
                "What combined-arms coordination must be rehearsed before execution?",
                "What sustainment or movement friction will break the plan first?",
            ],
        )


def build_gce_agent() -> GceAgent:
    return GceAgent()
