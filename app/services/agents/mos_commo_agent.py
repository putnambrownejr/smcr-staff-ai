from app.schemas.agents import AgentMetadata
from app.services.agents.base import PlaceholderAgent


def build_mos_commo_agent() -> PlaceholderAgent:
    return PlaceholderAgent(
        metadata=AgentMetadata(
            id="mos-commo",
            name="CommO MOS Agent",
            description="Supports communications planning checklists for reserve staff training contexts.",
            domain="communications",
            intended_users=["Communications officers", "S-6 staff", "SMCR staff"],
            allowed_sources=["public communications doctrine", "fictional/training scenarios"],
            disallowed_inputs=["COMSEC", "keying material", "real frequencies", "sensitive network data", "call signs"],
            system_prompt=(
                "Provide communications planning checklists while refusing sensitive technical/operational data."
            ),
        ),
        checklist=[
            "Draft PACE planning questions without real frequencies or call signs",
            "Identify C2 support assumptions and constraints",
            "Build radio/data/network planning checklist",
            "Flag spectrum, cyber, permissions, and COMSEC topics for authorized channels",
            "Account for reserve constraints: drill time, equipment access, licensing, currency, distributed personnel",
        ],
        follow_up_questions=[
            "Is the scenario fictional/training-only?",
            "Which public doctrine or SOP placeholder should the checklist map to?",
            "What reserve constraint is the limiting factor: time, equipment, permissions, or training currency?",
        ],
    )
