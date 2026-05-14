from app.chatgpt_bridge.schemas import BridgeCatalog, BridgeToolDefinition


def build_bridge_catalog() -> BridgeCatalog:
    return BridgeCatalog(
        tools=[
            BridgeToolDefinition(
                name="chief_brief_demo",
                title="Chief Brief Demo",
                description=(
                    "Use this when the user wants a concise drill, admin, document, and career triage brief."
                ),
                route="/demo/chief/brief",
                method="GET",
                notes=["Read-only", "Stateless demo route"],
            ),
            BridgeToolDefinition(
                name="career_watch_demo",
                title="Career Watch Demo",
                description=(
                    "Use this when the user wants PME, FitRep, opportunity, or self-development awareness."
                ),
                route="/demo/career/watch",
                method="GET",
                notes=["Read-only", "Stateless demo route"],
            ),
            BridgeToolDefinition(
                name="summarize_text_demo",
                title="Summarize Text Demo",
                description=(
                    "Use this when the user pastes notes or working text and wants summary, due-outs, "
                    "and follow-up questions."
                ),
                route="/demo/analysis/summarize",
                method="POST",
                input_schema={
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                        "focus": {"type": "string"},
                        "title": {"type": "string"},
                    },
                },
                notes=["Read-only", "Stateless demo route", "Does not store submitted text"],
            ),
            BridgeToolDefinition(
                name="draft_staff_product_demo",
                title="Draft Staff Product Demo",
                description=(
                    "Use this when the user needs an advisory OPORD, WARNO, FRAGO, SITREP, AAR, or "
                    "correspondence scaffold."
                ),
                route="/demo/staff-products/draft",
                method="POST",
                input_schema={
                    "type": "object",
                    "required": ["product_type", "topic"],
                    "properties": {
                        "product_type": {"type": "string"},
                        "topic": {"type": "string"},
                        "audience": {"type": "string"},
                        "training_or_fictional": {"type": "boolean"},
                    },
                },
                notes=["Read-only", "Stateless demo route", "Human-review guardrails apply"],
            ),
            BridgeToolDefinition(
                name="run_staff_agent_demo",
                title="Run Staff Agent Demo",
                description=(
                    "Use this when the user wants targeted help from a specific advisory staff or MOS agent."
                ),
                route="/demo/agents/{agent_id}/run",
                method="POST",
                input_schema={
                    "type": "object",
                    "required": ["agent_id", "input"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "input": {"type": "string"},
                        "context": {"type": "object"},
                    },
                },
                notes=["Read-only", "Stateless demo route", "Maps cleanly to a future MCP tool layer"],
            ),
        ],
        warnings=[
            "This bridge catalog is for stateless demo tools only.",
            "Personal/local tools should remain behind explicit runtime and auth boundaries.",
        ],
    )
