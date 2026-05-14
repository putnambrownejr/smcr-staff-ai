from pydantic import BaseModel, Field


class ChatGptToolSurfaceEntry(BaseModel):
    name: str
    route: str
    method: str
    purpose: str
    use_when: str
    read_only: bool = True
    stateless_demo: bool = True
    notes: list[str] = Field(default_factory=list)


class ChatGptToolSurfaceResponse(BaseModel):
    archetype: str
    mode: str
    tool_entries: list[ChatGptToolSurfaceEntry] = Field(default_factory=list)
    future_private_tools: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
