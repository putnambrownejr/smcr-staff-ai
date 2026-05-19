from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class BattleRhythmEntryInput(BaseModel):
    text: str = Field(min_length=1)
    section: str | None = None
    owner: str | None = None
    status: str = "open"
    suspense_date: str | None = None
    notes: list[str] = Field(default_factory=list)
    source: str | None = None


class BattleRhythmEntry(BattleRhythmEntryInput):
    entry_id: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BattleRhythmBoardResponse(BaseModel):
    user_key: str
    board_title: str
    source_title: str | None = None
    focus: list[str] = Field(default_factory=list)
    assumption_log: list[BattleRhythmEntry] = Field(default_factory=list)
    commander_decision_log: list[BattleRhythmEntry] = Field(default_factory=list)
    question_log: list[BattleRhythmEntry] = Field(default_factory=list)
    due_out_board: list[BattleRhythmEntry] = Field(default_factory=list)
    next_touchpoint: str | None = None
    context_note: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)


class BattleRhythmBoardUpsertRequest(BaseModel):
    board_title: str = Field(min_length=1)
    source_title: str | None = None
    focus: list[str] = Field(default_factory=list)
    assumption_log: list[BattleRhythmEntryInput] = Field(default_factory=list)
    commander_decision_log: list[BattleRhythmEntryInput] = Field(default_factory=list)
    question_log: list[BattleRhythmEntryInput] = Field(default_factory=list)
    due_out_board: list[BattleRhythmEntryInput] = Field(default_factory=list)
    next_touchpoint: str | None = None
    context_note: str | None = None
    warnings: list[str] = Field(default_factory=list)
