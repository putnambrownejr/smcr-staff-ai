from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    S2_REFERENCES,
    S3_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)
from app.schemas.training import ScenarioArchetype
from app.services.training.redcell_engine import build_redcell_design
from app.services.training.scenario_engine import infer_archetype_from_text


class RedTeamAssumptionsAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="red-team-assumptions-challenge",
            name="Red Team / Assumptions Challenge",
            description=(
                "Pressures staff logic, weak assumptions, fake COA differences, and polite groupthink before a plan "
                "hardens into an avoidable problem."
            ),
            domain="critical challenge",
            intended_users=["SMCR officers", "XO", "S-3", "planning teams", "command teams"],
            allowed_sources=[
                "public planning doctrine",
                "public command and staff PME references",
                "local training-only staff products",
            ],
            disallowed_inputs=[
                "classified operational details",
                "real-world targeting or sensitive movement details",
            ],
            system_prompt=(
                "Respond like a disciplined red-team officer working under a hard S-3. Be constructive, "
                "unsentimental, and specific. Challenge assumptions, false certainty, and cosmetic alternatives "
                "without becoming theatrical."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        archetype = _infer_archetype(input_text)
        redcell = build_redcell_design(
            archetype=archetype,
            actor_name="fictional adversary cell",
            place_name="the training area",
        )
        stereotype_lines = "\n".join(
            (
                f"- {item.label}: {item.summary}\n"
                f"  - indicators: {', '.join(item.indicators[:2])}\n"
                f"  - preferred seams: {', '.join(item.preferred_seams[:2])}\n"
                f"  - likely friendly mistakes: {', '.join(item.likely_friendly_mistakes[:2])}"
            )
            for item in redcell.stereotypes
        )
        question_lines = "\n".join(f"- {item}" for item in redcell.questions[:5])
        answer = (
            "Red-team / assumptions challenge advisory.\n\n"
            "Use this before the staff falls in love with its own draft.\n\n"
            f"Threat pattern read: `{archetype.value}`\n\n"
            "What to challenge:\n"
            "- Which assumption is carrying the most weight with the least evidence?\n"
            "- Which part of the concept fails first under friction?\n"
            "- Which adjacent section dependency is being treated like a given?\n"
            "- Are the COAs real alternatives or just wording changes?\n"
            "- What is the enemy, environment, or civil factor the staff is quietly hand-waving?\n\n"
            "Threat actor stereotype board:\n"
            f"{stereotype_lines}\n\n"
            "Red-team pattern:\n"
            "- Name the claim.\n"
            "- State why it may be weak.\n"
            "- Identify what would prove it wrong.\n"
            "- Recommend the smallest useful correction.\n\n"
            "Red-cell questions:\n"
            f"{question_lines}\n\n"
            "Helpful red-cell cuts:\n"
            "- If the adversary is probing, what routine are we showing it?\n"
            "- If the adversary wants overreaction, where are we easiest to bait?\n"
            "- If the adversary wants delay, which support or reporting seam buys it time fastest?\n"
            "- If the adversary wants confusion, what rumor or partial truth would the staff believe too quickly?\n\n"
            "Watch for soft failures:\n"
            "- Everyone agrees too quickly.\n"
            "- The plan depends on support that has not actually been confirmed.\n"
            "- Risk language exists, but nobody can say what would trigger a branch or abort.\n"
            "- The brief sounds polished because the hard part was edited out.\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
            structured_citations=structured_citations((*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES)),
            source_trust=source_trust_markers(
                (*STAFF_PROCESS_REFERENCES, *S2_REFERENCES, *S3_REFERENCES),
                notes_prefix=(
                    "Verify current planning and staff references before presenting this as a formal critique."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What assumption would most change the plan if it proved wrong?",
                "Which threat actor stereotype best fits the scenario, and what seam would that actor hit first?",
                "Which COA difference is currently more cosmetic than real?",
                "What failure trigger should the staff state explicitly?",
            ],
        )


def build_red_team_agent() -> RedTeamAssumptionsAgent:
    return RedTeamAssumptionsAgent()


def _infer_archetype(input_text: str) -> ScenarioArchetype:
    return infer_archetype_from_text(input_text)
