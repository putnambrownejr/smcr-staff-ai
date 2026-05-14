from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_maradmin_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="maradmin-monitor",
            name="MARADMIN Monitor Agent",
            description="Summarizes public MARADMIN and news items for reserve staff relevance.",
            domain="administration",
            intended_users=["SMCR officers", "staff officers", "admin staff"],
            allowed_sources=["Official Marine Corps public releases", "MARADMIN RSS/HTML"],
            disallowed_inputs=["PII", "classified information", "unit-sensitive plans"],
            system_prompt="Monitor public administrative messages and produce advisory summaries.",
        ),
        checklist=[
            "Identify audience and effective date",
            "Tag relevance",
            "List staff actions",
            "Flag human review items",
        ],
    )
