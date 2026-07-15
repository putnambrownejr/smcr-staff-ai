from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ChiefCapabilityOperation(StrEnum):
    read_summary = "read_summary"
    search_repository = "search_repository"
    append_travel_ledger = "append_travel_ledger"
    append_gtcc_check = "append_gtcc_check"
    append_fitrep_report = "append_fitrep_report"
    append_rs_profile = "append_rs_profile"
    append_fitrep_goal = "append_fitrep_goal"
    append_cadence = "append_cadence"


class ChiefCapabilityRequest(BaseModel):
    user_key: str = Field(min_length=1)
    operation: ChiefCapabilityOperation
    payload: dict[str, Any] = Field(default_factory=dict)


class ChiefCapabilityResponse(BaseModel):
    operation: ChiefCapabilityOperation
    result: Any
    changed: bool = False
    undo_token: str | None = None
    warnings: list[str] = Field(default_factory=list)
    footer: str = "DRAFT — Verify all references against current official sources before acting."


class ChiefDomainSummary(BaseModel):
    user_key: str
    travel_case_count: int = 0
    travel_ledger_entry_count: int = 0
    gtcc_check_count: int = 0
    fitrep_report_count: int = 0
    rs_profile_snapshot_count: int = 0
    fitrep_goal_count: int = 0
    private_cadence_count: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChiefUndoRequest(BaseModel):
    user_key: str = Field(min_length=1)
    undo_token: str = Field(min_length=1)


class ChiefUndoResponse(BaseModel):
    undo_token: str
    undone: bool
    message: str
