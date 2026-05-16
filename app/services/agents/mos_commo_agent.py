from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S6_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosCommoAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-commo",
            name="MOS CommO Advisor",
            description=(
                "Supports the S-6 / CommO lane with MOS-aware advisory help for communications planning, "
                "training readiness, and reserve comm friction while refusing sensitive technical detail."
            ),
            domain="communications support",
            intended_users=["CommO", "S-6 staff", "communications chiefs", "SMCR staff"],
            allowed_sources=[
                "public communications doctrine",
                "public command and control references",
                "public communications training references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "COMSEC",
                "keying material",
                "real frequencies",
                "sensitive network data",
                "call signs",
                "live cyber-defense procedures in unapproved environments",
            ],
            system_prompt=(
                "Respond like a reserve CommO working under the S-6. Focus on supportability, training "
                "readiness, permissions, operator currency, rehearsals, reporting discipline, and what fails "
                "first in a reserve comm plan. Stay generic on sensitive technical details."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS CommO advisory draft under the S-6 lane.\n\n"
            "Use this to shape communications planning, operator readiness, and training support, not as "
            "authoritative technical direction.\n\n"
            "What the MOS lane should add beyond the broad S-6 picture:\n"
            "- operator currency and who can actually execute the plan\n"
            "- equipment familiarity versus equipment ownership on paper\n"
            "- the gap between a clean PACE diagram and a rehearsed reporting rhythm\n"
            "- what the communications section must prep before drill instead of discovering it at first formation\n\n"
            "My read:\n"
            "- Reserve comm plans usually fail at the seams between access, setup time, operator reps, and "
            "unclear reporting discipline.\n"
            "- If the section has not rehearsed handover, fallback, and accountability, the gear itself is not "
            "the real problem.\n"
            "- Keep the plan simple enough that a tired section can execute it on a compressed drill timeline.\n\n"
            "CommO checklist:\n"
            "- Identify the supported event, essential reports, and information flow that actually matter.\n"
            "- Sort what requires trained operators, what requires licensed users, and what requires higher "
            "permissions or external support.\n"
            "- Confirm pre-drill tasks: charging, inventories, software or firmware checks, account access, "
            "vehicle comm checks, and local rehearsals.\n"
            "- Name what fallback method is real, available, and already understood by the users.\n"
            "- Treat CAC, middleware, browser auth, and portal readiness as part of the comm readiness problem.\n"
            "- End with operator tasks, section tasks, and command decisions instead of a generic equipment list.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(S6_REFERENCES),
            structured_citations=structured_citations(S6_REFERENCES),
            source_trust=source_trust_markers(
                S6_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-6 communications-support picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is the section short on operator reps, access, setup time, or permissions?",
                "What comm task must be rehearsed before drill rather than discovered during execution?",
                "What fallback method is real for this unit, not just decorative on a slide?",
                "What piece of support still belongs to the broader S-6 lane rather than the operator lane?",
            ],
        )


def build_mos_commo_agent() -> MosCommoAdvisorAgent:
    return MosCommoAdvisorAgent()
