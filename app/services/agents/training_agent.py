from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_training_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="training-planner",
            name="Training Planner Agent",
            description="Builds advisory training planning checklists and readiness reminders.",
            domain="training",
            intended_users=["TrainingO", "company staff", "battalion staff"],
            allowed_sources=["public T&R references", "public policy"],
            disallowed_inputs=["private readiness rosters", "PII"],
            system_prompt="Assist training planning while requiring authoritative review.",
        ),
        checklist=[
            "Identify training objective",
            "Map prerequisites",
            "Reserve resources",
            "Plan after-action capture",
        ],
    )
