"""Virtual staff round table schemas.

A round table runs multiple staff agents against the same scenario or
training-product request. The opening round runs participants concurrently
and independently; an optional cross-review round re-runs each participant
with every other participant's structured assessment; a synthesizer agent
(Chief of Staff by default) integrates the final picture.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.external_processing import ExternalProcessingApproval


class RoundtableRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": (
                    "A magnitude 7.1 earthquake struck a partner nation capital. "
                    "500 casualties, 10,000 displaced, the port is damaged, and a "
                    "MEU supports FHADR operations."
                ),
                "context": {"request_is_training_or_fictional": True},
            }
        }
    )
    scenario: str = Field(min_length=1)
    agents: list[str] = Field(
        default_factory=list,
        description="Participant agent ids. Empty list selects participants by `preset`.",
    )
    preset: Literal["auto", "full_staff", "training", "command_team"] = Field(
        default="auto",
        description=(
            "Who sits at the table when `agents` is empty. 'auto' = core seats plus sections triggered by the "
            "scenario text, falling back to the full staff when nothing specific is triggered; 'full_staff' = "
            "every staff seat plus the planning, ORM, and red-team advisors; 'training' = the seats that build "
            "and run a drill or exercise; 'command_team' = XO, OpsO, SEL, S-1, SJA, chaplain, planning, red team."
        ),
    )
    inference: Literal["auto", "local", "external"] = Field(
        default="auto",
        description=(
            "'auto' = every seat answers through the configured external AI (behind the approval preview) "
            "when one is configured, otherwise from local doctrine templates; 'local' = templates only; "
            "'external' = require the external path (returns the unavailable notice if none is configured)."
        ),
    )
    rounds: int = Field(
        default=2,
        ge=1,
        le=2,
        description="1 = opening assessments only; 2 = opening + cross-review with shared assessments.",
    )
    synthesizer: str | None = Field(
        default="chief-of-staff",
        description="Agent that integrates all assessments last. Null skips synthesis.",
    )
    context: dict[str, Any] = Field(default_factory=dict)
    external_processing_approval: ExternalProcessingApproval | None = None


class RoundtableCapability(BaseModel):
    """What the round table can honestly do on this install."""

    external_available: bool
    model: str | None = None
    provider_base_url: str | None = None
    note: str


class RoundtablePacketRequest(BaseModel):
    scenario: str = Field(min_length=1)
    agents: list[str] = Field(default_factory=list)
    preset: Literal["auto", "full_staff", "training", "command_team"] = "full_staff"
    synthesizer: str | None = "chief-of-staff"
    kind: Literal["roundtable", "chain"] = "roundtable"
    include_role_notes: bool = True
    save: bool = False
    user_key: str | None = None
    title: str | None = None


class RoundtablePacketResponse(BaseModel):
    kind: str
    participants: list[str]
    participant_names: list[str]
    synthesizer: str | None = None
    packet_markdown: str
    saved_doc_id: str | None = None
    saved_category: str | None = None
    note: str


class RoundtableEntry(BaseModel):
    agent_id: str
    answer: str
    scenario_output: dict[str, Any] | None = None
    scenario_output_status: str = "not_applicable"
    confidence: str = "low"
    follow_up_questions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RoundtableRound(BaseModel):
    name: str
    entries: list[RoundtableEntry]


class RoundtableResponse(BaseModel):
    scenario: str
    mode: Literal["external_ai", "local_templates"] = "local_templates"
    participants: list[str]
    auto_selected: list[str] = Field(default_factory=list)
    rounds: list[RoundtableRound]
    synthesis: RoundtableEntry | None = None
    assessments: dict[str, Any] = Field(
        default_factory=dict,
        description="Final structured assessments keyed by staff role (g9, s2, s4, s6, planning, cos).",
    )
    warnings: list[str] = Field(default_factory=list)
