from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_0402_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosLogistics0402AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-logistics-0402",
            name="MOS 0402 / Logistics Officer Advisor",
            description=(
                "Supports the S-4 lane with MOS-aware 0402 advisory help for supportability, sustainment, "
                "movement, maintenance, and logistics training realism."
            ),
            domain="logistics support",
            intended_users=["LogO", "S-4 staff", "planners", "SMCR officers"],
            allowed_sources=[
                "public logistics doctrine",
                "public logistics training references",
                "public logistics schoolhouse references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified movement data",
                "real-world convoy details",
                "sensitive supply locations",
                "operationally sensitive sustainment details",
            ],
            system_prompt=(
                "Respond like a reserve 0402 working under the S-4. Act like the narrower MOS execution slice of "
                "the broader S-4 picture. Focus on supportability, sustainment judgment, sequencing, lead times, "
                "maintenance and distribution friction, and the point where an under-resourced plan stops being real."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 0402 logistics officer advisory draft under the S-4 lane.\n\n"
            "Use this to shape supportability and sustainment thinking, not as authoritative logistics tasking.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-4 owns the broad logistics picture, support relationships, and command supportability call.\n"
            "- The 0402 lane owns the narrower officer judgment on whether the support concept actually works, "
            "what breaks first, and what must be resourced or sequenced earlier.\n\n"
            "What the MOS lane should add beyond the broad S-4 picture:\n"
            "- a harder read on lead times, support priorities, and sustainment assumptions\n"
            "- the difference between a support request and a supportable plan\n"
            "- how movement, maintenance, ammo, chow, billeting, and accountability interact in reality\n"
            "- what the logistics estimate should say before the XO hears a polished fantasy\n\n"
            "My read:\n"
            "- 0402 value is not just listing classes of supply. It is killing unresourced optimism early.\n"
            "- Most reserve logistics pain starts before execution: late requests, vague ownership, and nobody "
            "naming the longest lead-time problem.\n"
            "- If the sustainment concept depends on people improvising after arrival, the concept is weak.\n\n"
            "0402 checklist:\n"
            "- Name the supported event, critical support requirements, and the first no-fail item.\n"
            "- Separate essential support from convenience support.\n"
            "- Identify what requires early coordination with S-3, S-6, medical, range, transport, or higher.\n"
            "- Make the logistics estimate answer what cancels the event, what degrades it, and what is recoverable.\n"
            "- End with decisions, due-outs, and supportability red lines instead of a generic supply list.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_0402_REFERENCES),
            structured_citations=structured_citations(MOS_0402_REFERENCES),
            source_trust=source_trust_markers(
                MOS_0402_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-4 supportability and sustainment picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What support item or lead time is most likely to break this plan first?",
                "What part of the sustainment concept is still assumed rather than confirmed?",
                "What decision must the command make earlier to keep this supportable?",
                "What still belongs to the broader S-4 lane rather than the 0402 estimate slice?",
            ],
        )


def build_mos_logistics_0402_agent() -> MosLogistics0402AdvisorAgent:
    return MosLogistics0402AdvisorAgent()
