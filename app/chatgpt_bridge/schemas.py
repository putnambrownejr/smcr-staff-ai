from pydantic import BaseModel, Field


class BridgeToolDefinition(BaseModel):
    name: str
    title: str
    description: str
    route: str
    method: str
    read_only: bool = True
    stateless_demo: bool = True
    input_schema: dict[str, object] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class BridgeCatalog(BaseModel):
    archetype: str = "tool-only"
    mode: str = "stateless_demo_first"
    tools: list[BridgeToolDefinition] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
