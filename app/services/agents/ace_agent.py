from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_7200_REFERENCES,
    ORM_REFERENCES,
    S3_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class AceAgent(Agent):
    def __init__(self) -> None:
        refs = S3_REFERENCES + ORM_REFERENCES + STAFF_PRODUCT_REFERENCES + MOS_7200_REFERENCES
        self.metadata = AgentMetadata(
            id="ace",
            name="ACE / Air Combat Element",
            description=(
                "MAGTF Air Combat Element representative — air support, aviation effects, airspace coordination, "
                "air-ground integration, and ACE sustainment considerations."
            ),
            domain="aviation and air combat element",
            intended_users=["SMCR officers", "FSOs", "AirOs", "S-3", "wing staff", "ACE planners"],
            allowed_sources=[
                "public aviation and air-ground doctrine",
                "public training and readiness references",
                "training-only air support scenarios",
            ],
            disallowed_inputs=[
                "classified air tasking orders",
                "real-world flight schedules or sortie data",
                "sensitive airspace control measures",
                "live NOTAM or DAFIF data for real operations",
            ],
            system_prompt=(
                "Respond like an ACE representative advising the MAGTF CE. Focus on supported effects, "
                "air-ground integration, and coordination discipline. Stay training-safe and advisory."
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
            "ACE / Air Combat Element advisory draft.\n\n"
            "Use this to shape air-ground integration and ACE coordination, not to replace "
            "qualified aviation planners, local SOPs, or formal airspace coordination.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- Start with the supported effect, not the aircraft wish list.\n"
            "- Air-ground integration becomes fragile when airspace, control, comm, fires, safety, "
            "and timelines are handled as separate conversations.\n"
            "- Keep real-world tasking details out of this tool.\n\n"
            "Primary ACE lenses:\n"
            "- What aviation effect supports the exercise objective or commander decision?\n"
            "- What airspace, fires, comm, range-control, and safety deconfliction must be solved first?\n"
            "- What request, approval, or support relationship has the longest lead time?\n"
            "- What no-go condition should stop the aviation portion?\n"
            "- How does the ACE sustain itself during the event (maintenance, crews, fuel, ordnance)?\n\n"
            "7200 Aviation Officer depth:\n"
            "- Whether the training event is supportable by aircraft, crews, maintenance, ranges, and weather.\n"
            "- Whether safety and ORM concerns are being handled as command decisions.\n"
            "- Whether MAWTS-style standardization and debrief discipline are being considered.\n"
            "- Whether wing staff sections can preserve continuity across drill gaps.\n\n"
            "Checklist:\n"
            "- Build an air support estimate with supported effect, control method, comm/PACE.\n"
            "- Establish deconfliction questions, required approvals, and branch/no-go criteria.\n"
            "- Coordinate with S-3, fires, S-6, safety, GCE, LCE, and range/control authorities.\n"
            "- Rehearse air-ground coordination before execution.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(
                self._refs,
                notes_prefix="Verify current aviation doctrine and local coordination requirements.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What aviation effect supports the exercise objective?",
                "What airspace, fires, and comm deconfliction must be solved first?",
                "What request or approval has the longest lead time?",
                "What no-go condition should stop the aviation portion?",
            ],
        )


def build_ace_agent() -> AceAgent:
    return AceAgent()
