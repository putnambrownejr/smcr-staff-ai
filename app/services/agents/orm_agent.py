from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_orm_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="orm-risk-management",
            name="ORM / Risk Management Agent",
            description="Produces advisory risk prompts and ORM checklist drafts.",
            domain="safety",
            intended_users=["Safety officers", "staff officers", "leaders"],
            allowed_sources=["public risk management doctrine", "training scenario inputs"],
            disallowed_inputs=["medical PII", "real mishap details requiring protected handling"],
            system_prompt="Prompt structured risk thinking without replacing formal safety review.",
        ),
        checklist=[
            "Identify hazards",
            "Assess severity/probability",
            "Develop controls",
            "Assign supervision and residual-risk owner",
        ],
    )
