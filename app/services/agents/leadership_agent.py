from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_leadership_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="leadership-advisor",
            name="Leadership Advisor",
            description="Provides reflective leadership prompts grounded in public doctrine when connected to RAG.",
            domain="leadership",
            intended_users=["officers", "SNCOs", "staff leaders"],
            allowed_sources=["public leadership doctrine"],
            disallowed_inputs=["protected investigations", "private personnel disputes"],
            system_prompt="Offer reflective prompts and options while encouraging human judgment.",
        ),
        checklist=[
            "Clarify intent",
            "Consider Marines affected",
            "Identify communication plan",
            "Seek mentor/chain input when appropriate",
        ],
    )
