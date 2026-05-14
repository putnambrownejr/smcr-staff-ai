from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_fitrep_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="fitrep-assistant",
            name="FitRep Assistant",
            description="Helps outline PES/FitRep drafting considerations without storing personal evaluations.",
            domain="performance evaluation",
            intended_users=["officers", "reporting seniors", "reviewing officers"],
            allowed_sources=["public PES references"],
            disallowed_inputs=["SSNs", "medical data", "sensitive personnel files"],
            system_prompt="Support drafting structure and review prompts, not final ratings decisions.",
        ),
        checklist=[
            "Confirm reporting occasion",
            "Check billet accomplishments",
            "Avoid unsupported claims",
            "Route for official review",
        ],
    )
