from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_mos_civil_affairs_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="mos-civil-affairs",
            name="Civil Affairs Officer MOS Agent",
            description="Supports civil affairs planning checklists and public-source research framing.",
            domain="civil affairs",
            intended_users=["Civil affairs officers", "CA staff", "planners"],
            allowed_sources=["public CA/CMO doctrine", "public population/context sources"],
            disallowed_inputs=[
                "classified assessments",
                "targeting",
                "private personal data",
                "sensitive partner details",
            ],
            system_prompt="Provide advisory CA planning checklists, not authoritative plans or sensitive assessments.",
        ),
        checklist=[
            "Frame civil reconnaissance objectives",
            "Plan civil information management categories",
            "Prepare key leader engagement questions",
            "Identify interagency coordination considerations",
            "Account for reserve constraints: continuity, local familiarity, partner access, pre-mobilization training",
        ],
        follow_up_questions=[
            "Is this a fictional/training planning problem?",
            "Which public area or population sources should be cited later?",
            "What continuity handoff is needed between drill periods?",
        ],
    )
