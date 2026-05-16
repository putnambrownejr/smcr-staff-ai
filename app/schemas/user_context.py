from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ActiveUserContext(BaseModel):
    user_key: str
    unit_name: str | None = None
    unit_type: str | None = None
    unit_family: str | None = None
    billet_override: str | None = None
    mos_override: str | None = None
    current_focus: list[str] = Field(default_factory=list)
    staff_bias: list[str] = Field(default_factory=list)
    temporary_notes: list[str] = Field(default_factory=list)
    preferences: dict[str, str] = Field(default_factory=dict)
    expires_at: datetime | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)


class ActiveUserContextUpsertResponse(BaseModel):
    active_user_context: ActiveUserContext
    message: str
