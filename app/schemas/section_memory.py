from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SectionMemoryEntry(BaseModel):
    section: str = Field(min_length=1)
    title: str = Field(min_length=1)
    recurring_questions: list[str] = Field(default_factory=list)
    recurring_failure_modes: list[str] = Field(default_factory=list)
    preferred_checks: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SectionMemoryProfile(BaseModel):
    user_key: str
    entries: list[SectionMemoryEntry] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[str] = Field(default_factory=list)


class SectionMemoryProfileUpsertRequest(BaseModel):
    entries: list[SectionMemoryEntry] = Field(default_factory=list)


class SectionMemoryUpsertResponse(BaseModel):
    profile: SectionMemoryProfile
    message: str
