from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_drill_prep_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="drill-prep-calendar",
            name="Drill Prep Calendar Agent",
            description="Creates advisory drill-prep timelines and reminder tasks.",
            domain="reserve administration",
            intended_users=["SMCR officers", "company staff", "battalion staff"],
            allowed_sources=["local calendar data", "public training requirements"],
            disallowed_inputs=["calendar tokens", "PII not required for planning"],
            system_prompt="Turn drill dates into practical advisory preparation timelines.",
        ),
        checklist=[
            "Uniform and grooming prep",
            "Travel and DTS reminders",
            "Medical readiness check",
            "Training/PME reminders",
        ],
    )
