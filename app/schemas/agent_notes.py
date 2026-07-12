from __future__ import annotations

from pydantic import BaseModel, Field


class AgentNotesResponse(BaseModel):
    agent_notes: dict[str, str] = Field(default_factory=dict)
    skill_notes: dict[str, str] = Field(default_factory=dict)


class AgentNoteUpdateRequest(BaseModel):
    note: str = ""
