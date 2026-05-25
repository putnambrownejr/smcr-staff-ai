from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S6_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class S6CommunicationsAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="s6-comms",
            name="S-6 / Communications Advisor",
            description=(
                "Supports reserve C2 support planning, PACE framing, supportability checks, and "
                "communications coordination while refusing sensitive technical detail. Includes PKI/CAC "
                "troubleshooting as an S-6 user-access support lane and CommO/MOS-commo concerns as a "
                "subordinate operator-readiness lane."
            ),
            domain="communications support",
            intended_users=["SMCR officers", "S-6", "CommO", "OpsO", "command teams"],
            allowed_sources=[
                "public communications doctrine",
                "public command and control references",
                "public communications training references",
                "public operations-planning references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "COMSEC",
                "keying material",
                "real frequencies",
                "sensitive network data",
                "call signs",
            ],
            system_prompt=(
                "Respond like a practical reserve S-6. Focus on C2 support, PACE planning, supportability, "
                "permissions, and information flow while refusing sensitive technical details. Treat PKI, CAC, "
                "middleware, and portal access issues as part of the S-6 user-support lane. Be blunt about what "
                "will fail first."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"
        answer = (
            "S-6 advisory draft.\n\n"
            "Use this to shape communications support and C2 planning, not as authoritative technical direction.\n\n"
            f"{active_context_block}"
            "Bottom line:\n"
            "- If nobody knows how the unit will pass information when the primary method fails,\n"
            "  then the comm plan is decorative, not real.\n\n"
            "Primary S-6 lenses:\n"
            "- What communications support is essential to command and control?\n"
            "- What assumptions exist about equipment, permissions, training currency, and support windows?\n"
            "- What fallback methods are available if the preferred plan degrades?\n"
            "- What user-access risks exist around CAC, PKI, middleware, browser auth, or portal readiness?\n"
            "- Which concerns belong in the broader S-6 staff lane versus the narrower CommO/operator lane?\n"
            "- What should remain generic until validated through proper channels?\n\n"
            "My read:\n"
            "- In reserve units, the quiet killers are access, permissions, stale gear, and lack of rehearsal.\n"
            "- The first comm failure is usually not a radio; it is confusion about\n"
            "  report windows, fallback, or who owns the net.\n"
            "- Keep the plan commercial/training-safe, simple enough to brief, and easy enough to rehearse.\n\n"
            "Checklist:\n"
            "- Define the supported event and essential C2 effect.\n"
            "- Build a generic PACE matrix with primary, alternate, contingency, and emergency methods;\n"
            "  include switch criteria, owner, acknowledgement rule, and missed-report action.\n"
            "- Build a radio guard chart that names guard periods, responsible stations, report windows,\n"
            "  escalation triggers, and closeout/AAR capture without real frequencies or call signs.\n"
            "- Build the comm plan around information flow first: who reports what, to whom, by when,\n"
            "  with what acknowledgement and fallback.\n"
            "- Identify what information must move, who must receive it, and how long delay is acceptable.\n"
            "- Check equipment access, licensing, permissions, and training currency early.\n"
            "- Reduce reporting methods before the event; too many methods usually means\n"
            "  nobody is sure which one matters.\n"
            "- Treat CAC, certificate, middleware, and portal access issues as S-6 support problems.\n"
            "- Escalate to a local help desk or enterprise support channel when needed.\n"
            "- Identify follow-up actions with owners before leaving drill.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S6_REFERENCES),
            structured_citations=structured_citations(S6_REFERENCES),
            source_trust=source_trust_markers(
                S6_REFERENCES,
                notes_prefix=(
                    "Verify current command-and-control and communications references "
                    "before finalizing support assumptions."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What supported event or commander decision needs communications support?",
                "What reserve friction matters most here: equipment, permissions, support time, or training currency?",
                "What report windows and missed-report triggers should the radio guard chart enforce?",
                "Is there a CAC, certificate, or portal-access issue that should be handled in the S-6 lane first?",
                "What generic fallback methods exist if the primary approach fails?",
            ],
        )


def build_s6_comms_agent() -> S6CommunicationsAdvisorAgent:
    return S6CommunicationsAdvisorAgent()
