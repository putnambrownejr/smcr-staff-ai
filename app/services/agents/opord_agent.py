from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_opord_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="doctrine-opord-assistant",
            name="Doctrine / OPORD Assistant",
            description="Provides public-doctrine-grounded OPORD templates and planning checklists.",
            domain="operations planning",
            intended_users=["staff officers", "commanders"],
            allowed_sources=["public doctrine", "training-only fictional scenarios"],
            disallowed_inputs=["real-world current operations", "classified plans", "exact movements"],
            system_prompt="Provide templates and checklists, never authoritative operational orders.",
        ),
        checklist=[
            "Clarify training-only assumptions",
            "Use five-paragraph order structure",
            "Identify annexes",
            "Require commander/staff validation",
        ],
    )
