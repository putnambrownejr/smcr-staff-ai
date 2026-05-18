from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ReadingProgressStatus(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class ReadingProgressRecord(BaseModel):
    user_key: str
    slug: str
    title: str
    author: str
    status: ReadingProgressStatus = ReadingProgressStatus.not_started
    notes: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None


class UpsertReadingProgressRequest(BaseModel):
    status: ReadingProgressStatus
    notes: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class ReadingProgressListResponse(BaseModel):
    user_key: str
    records: list[ReadingProgressRecord] = Field(default_factory=list)
