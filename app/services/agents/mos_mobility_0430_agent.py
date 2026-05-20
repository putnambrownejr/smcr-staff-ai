from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MOS_0430_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MosMobility0430AdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="mos-mobility-0430",
            name="MOS 0430 / Mobility Officer Advisor",
            description=(
                "Supports the S-4 lane with MOS-aware 0430 advisory help for embarkation, strategic mobility, "
                "deployment flow, and movement-control discipline."
            ),
            domain="mobility support",
            intended_users=["Mobility officers", "Embarkation planners", "S-4 staff", "SMCR officers"],
            allowed_sources=[
                "public logistics doctrine",
                "public mobility and embarkation training references",
                "public transportation and distribution references",
                "training-only scenarios",
            ],
            disallowed_inputs=[
                "classified deployment plans",
                "exact real-world movement schedules",
                "sensitive port or load plans",
                "operationally sensitive embarkation details",
            ],
            system_prompt=(
                "Respond like a reserve 0430 working under the S-4. Act like the narrower mobility and embarkation "
                "slice of the broader logistics picture. Focus on deployability, movement-control discipline, "
                "documentation, sequencing, and where the plan dies when lift, packaging, or reporting is sloppy."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "MOS 0430 mobility officer advisory draft under the S-4 lane.\n\n"
            "Use this to shape mobility, embarkation, and movement-control thinking, not as authoritative movement "
            "direction.\n\n"
            "Relationship to the parent lane:\n"
            "- The S-4 owns the broad sustainment and supportability picture.\n"
            "- The 0430 lane owns the narrower mobility fight: embarkation discipline, movement documentation, "
            "FDP&E logic, sequencing, and whether the unit can actually move what it says it can move.\n\n"
            "What the MOS lane should add beyond the broad S-4 picture:\n"
            "- whether the force list, lift assumptions, and movement documentation match reality\n"
            "- whether the unit knows what loads first, what cannot be delayed, and what can be left behind\n"
            "- whether embarkation tasks are resourced early enough instead of becoming a last-week panic\n"
            "- whether reporting and coordination are clean enough for higher headquarters to trust the plan\n\n"
            "My read:\n"
            "- The mobility fight is usually lost in packaging, documentation, and sequencing long before the convoy "
            "or aircraft shows up.\n"
            "- If nobody owns ITV, load discipline, and the movement paperwork, the unit is not deployable just "
            "because the gear exists.\n"
            "- Reserve units get hurt here when embarkation becomes an annual memory test instead of a "
            "maintained skill.\n\n"
            "0430 checklist:\n"
            "- Identify the force, lift, documentation, and sequencing problem in one clean statement.\n"
            "- Separate strategic or operational movement issues from simple local transport problems.\n"
            "- Confirm who owns movement data, embarkation prep, load priorities, and higher-headquarters reporting.\n"
            "- Name what packaging, hazardous-material, or accountability issue can stop movement cold.\n"
            "- End with movement decisions, due-outs, and missing mobility data instead of generic optimism.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MOS_0430_REFERENCES),
            structured_citations=structured_citations(MOS_0430_REFERENCES),
            source_trust=source_trust_markers(
                MOS_0430_REFERENCES,
                notes_prefix="Use this MOS lane under the broader S-4 logistics and movement-support picture.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "Is this mainly a local transport issue, an embarkation issue, or a broader mobility-planning issue?",
                "What document, load priority, or reporting step is least controlled right now?",
                "What has to be decided early so movement does not become a last-minute scramble?",
                "What still belongs to the broad S-4 lane rather than the 0430 mobility slice?",
            ],
        )


def build_mos_mobility_0430_agent() -> MosMobility0430AdvisorAgent:
    return MosMobility0430AdvisorAgent()
