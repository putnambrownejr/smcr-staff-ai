from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_uniform_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="uniform-advisor",
            name="Uniform Advisor Agent",
            description=(
                "Provides advisory uniform-prep checklists grounded in public regulations when connected to RAG."
            ),
            domain="uniforms",
            intended_users=["SMCR Marines", "staff officers"],
            allowed_sources=["Public uniform regulations", "public MARADMINs"],
            disallowed_inputs=["disciplinary PII", "private personnel records"],
            system_prompt="Provide non-authoritative uniform preparation guidance with citations when available.",
        ),
        checklist=[
            "Confirm event uniform",
            "Check seasonal guidance",
            "Inspect serviceability",
            "Route ambiguous cases to chain of command",
        ],
    )
