from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    ORM_REFERENCES,
    S3_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class AirOAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="airo-advisor",
            name="AirO Advisor",
            description=(
                "Supports reserve-focused aviation coordination, air support planning questions, and "
                "air-ground integration checklists for staff planning."
            ),
            domain="aviation support",
            intended_users=["AirO", "S-3", "staff officers", "command teams"],
            allowed_sources=[
                "public aviation support doctrine",
                "public operations-planning doctrine",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "real current air tasking details",
                "classified aviation operations",
                "exact movements or sensitive aviation coordination data",
            ],
            system_prompt=(
                "Provide advisory air-support planning and coordination checklists "
                "for training or public planning contexts. Stay generic and require human review."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        refs = S3_REFERENCES + ORM_REFERENCES
        answer = (
            "AirO exercise planning advisory.\n\n"
            "Use this to build an aviation-support estimate for a training or exercise plan. It is not aviation "
            "tasking, airspace control direction, fires clearance, or approval to execute.\n\n"
            "Supported aviation effect:\n"
            "- State the effect first: lift, observation, assault support, close-air-support familiarization, "
            "CASEVAC support discussion, C2 relay, or aviation-awareness training.\n"
            "- Tie the effect to the supported unit, training objective, commander decision, and assessment method.\n"
            "- Separate nice-to-have aviation exposure from support that is critical to exercise realism.\n\n"
            "Air-ground coordination matrix:\n"
            "- S-3: event timeline, training objectives, support request status, rehearsals, and AAR criteria.\n"
            "- Fires/range control: surface danger zones, airspace questions, clearance boundaries, and "
            "abort criteria.\n"
            "- S-6: comm/PACE, plain-language reporting flow, lost-comm action, and user training needs.\n"
            "- Safety/ORM: aviation-specific hazards, weather/visibility assumptions, med plan, and risk owner.\n"
            "- GCE/LCE: pickup/drop-off assumptions, movement windows, landing-zone support, and recovery friction.\n\n"
            "Deconfliction and no-go questions:\n"
            "- What airspace, control, range, fires, ground movement, and public-affairs constraints must be solved "
            "before the event can be called executable?\n"
            "- Who is the qualified aviation reviewer, and what is their latest useful review point?\n"
            "- What branch preserves training value if aviation support is cancelled, delayed, or reduced?\n"
            "- What condition stops the aviation portion instead of forcing unsafe or fake training?\n\n"
            "Resource lookup path:\n"
            "- Start with MCPP and command-and-staff-action references for estimate discipline.\n"
            "- Use safety/ORM references for risk ownership and no-go criteria.\n"
            "- Verify any actual aviation support, airspace, range, or control requirement through current command "
            "channels and qualified aviation personnel."
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(refs),
            structured_citations=structured_citations(refs),
            source_trust=source_trust_markers(
                refs,
                notes_prefix="Verify current aviation, range, airspace, and safety applicability before action.",
            ),
            confidence=Confidence.low,
            follow_up_questions=[
                "Is this a training event, exercise support problem, or planning estimate?",
                "What supported effect or decision are you trying to enable?",
                "Which staff sections must coordinate before this becomes a real request?",
            ],
        )


def build_airo_agent() -> AirOAdvisorAgent:
    return AirOAdvisorAgent()
