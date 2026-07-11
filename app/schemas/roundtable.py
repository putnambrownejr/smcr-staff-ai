"""Virtual staff round table schemas.

A round table runs multiple staff agents against the same scenario or
training-product request. The opening round runs participants concurrently
and independently; an optional cross-review round re-runs each participant
with every other participant's structured assessment; a synthesizer agent
(Chief of Staff by default) integrates the final picture.
"""

from __future__ import annotations

from typing import Any

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
        description="Participant agent ids. Empty list auto-selects participants from the scenario content.",
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
    participants: list[str]
    auto_selected: list[str] = Field(default_factory=list)
    rounds: list[RoundtableRound]
    synthesis: RoundtableEntry | None = None
    assessments: dict[str, Any] = Field(
        default_factory=dict,
        description="Final structured assessments keyed by staff role (g9, s2, s4, s6, planning, cos).",
    )
    warnings: list[str] = Field(default_factory=list)
