from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ChiefSetup(BaseModel):
    """Standing context a user configures for their Chief of Staff.

    Persisted per user (see ChiefSetupStore) so the dashboard remembers it and
    the same inputs can be rendered into a portable "Chief of Staff" briefing
    block for any external chatbot (see build_chief_briefing_block).
    """

    user_key: str
    unit: str = ""
    billet: str = ""
    echelon: str = ""
    drill_schedule: str = ""
    commander_intent: str = ""
    priorities: list[str] = Field(default_factory=list)
    battle_rhythm: list[str] = Field(default_factory=list)
    watch_items: list[str] = Field(default_factory=list)
    output_format: str = "Naval letter"
    tone: str = "Direct and professional"
    standing_notes: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChiefSetupUpsertRequest(BaseModel):
    unit: str = ""
    billet: str = ""
    echelon: str = ""
    drill_schedule: str = ""
    commander_intent: str = ""
    priorities: list[str] = Field(default_factory=list)
    battle_rhythm: list[str] = Field(default_factory=list)
    watch_items: list[str] = Field(default_factory=list)
    output_format: str = "Naval letter"
    tone: str = "Direct and professional"
    standing_notes: str = ""


class ChiefSetupResponse(BaseModel):
    setup: ChiefSetup
    briefing_block: str
    is_configured: bool
