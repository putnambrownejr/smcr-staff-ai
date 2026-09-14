"""User-defined automations: saved staff routines rendered into portable AI prompts.

An automation is a standing instruction the user builds once (name, trigger,
cadence, steps, seats to consult, inputs, output format). The app stores it,
renders it into a copy-paste block for any chatbot, and can wrap a run (the
user's input for this occurrence) into a staff call packet. The app never
executes the automation itself.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AutomationUpsertRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    purpose: str = ""
    trigger: str = ""
    cadence: str = ""
    agents: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    inputs_needed: list[str] = Field(default_factory=list)
    output_format: str = "Bullet summary with a table of actions"
    tone: str = "Direct and professional"
    standing_notes: str = ""
    template_key: str | None = None


class Automation(AutomationUpsertRequest):
    id: str
    user_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AutomationTemplate(BaseModel):
    key: str
    name: str
    purpose: str
    trigger: str
    cadence: str
    agents: list[str]
    steps: list[str]
    inputs_needed: list[str]
    output_format: str


class AutomationResponse(BaseModel):
    automation: Automation
    block: str
    agent_names: list[str]


class AutomationListResponse(BaseModel):
    automations: list[AutomationResponse]


class AutomationPacketRequest(BaseModel):
    input: str = Field(min_length=1)
    save: bool = False
    include_role_notes: bool = True


class AutomationPacketResponse(BaseModel):
    automation_id: str
    name: str
    participants: list[str]
    participant_names: list[str]
    packet_markdown: str
    saved_doc_id: str | None = None
    note: str
