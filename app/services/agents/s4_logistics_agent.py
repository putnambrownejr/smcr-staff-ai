from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S4_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class S4LogisticsAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s4-logistics",
            name="S-4 / Logistics Advisor",
            description=(
                "Supports reserve logistics planning, movement, sustainment, supply, maintenance, and "
                "supportability checks for staff planning."
            ),
            domain="logistics",
            intended_users=["SMCR officers", "S-4", "LogO", "S-3", "Chief of Staff / Aide"],
            allowed_sources=[
                "public logistics doctrine",
                "public logistics training references",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified movement plans",
                "sensitive supply or transport details",
                "real-world exact convoy or sustainment details in unapproved environments",
            ],
            system_prompt=(
                "Respond like a practical reserve S-4/LogO. Focus on supportability, sustainment, movement, "
                "maintenance, supply, and friction points. Call out fantasy assumptions early, identify the "
                "longest lead-time item first, and stay advisory. Sound like the officer who kills unresourced "
                "optimism before it burns the unit."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "S-4 / logistics advisory draft.\n\n"
            "Use this to shape reserve logistics planning, not as authoritative movement or support direction.\n\n"
            "Bottom line:\n"
            "- If transport, billeting, chow, ammo, comm support, medical support, or accountability is shaky,\n"
            "  the plan is not ready no matter how good it looks on the whiteboard.\n\n"
            "Primary S-4 lenses:\n"
            "- What support must be in place for this event or plan to work at all?\n"
            "- What movement, billeting, chow, comm support, fuel, supply, maintenance, or medical assumptions exist?\n"
            "- What has the longest lead time and therefore needs the earliest decision?\n"
            "- What reserve-specific friction will show up because people, gear, and support are distributed?\n\n"
            "My read:\n"
            "- The hardest logistics problem usually hides in accountability, travel timing,\n"
            "  or late support requests.\n"
            "- Nice ideas die when nobody owns vehicles, billeting, ammo, or issue/turn-in windows.\n"
            "- If the longest lead-time item is still vague, the plan is still a concept, not a supported event.\n\n"
            "Checklist:\n"
            "- Identify critical support requirements, lead times, and approval points.\n"
            "- Separate must-have sustainment from nice-to-have convenience requests.\n"
            "- Confirm transport, billeting, equipment, and accountability assumptions.\n"
            "- Flag maintenance, ammo, communications, and medical dependencies early.\n"
            "- Call out what cancels the event, what degrades it, and what merely inconveniences it.\n"
            "- Build follow-up actions with owners and suspense dates before leaving drill.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S4_REFERENCES),
            structured_citations=structured_citations(S4_REFERENCES),
            source_trust=source_trust_markers(
                S4_REFERENCES,
                notes_prefix="Verify current logistics and movement references before committing support assumptions.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this a drill, AT, range, convoy, or field-support problem?",
                "What support item or lead time is most likely to break the plan first?",
                "Which sections need to coordinate for this to become supportable?",
            ],
        )


def build_s4_logistics_agent() -> S4LogisticsAdvisorAgent:
    return S4LogisticsAdvisorAgent()
