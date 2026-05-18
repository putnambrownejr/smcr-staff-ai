from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.ingestion import MessageRecord


class CustomWatchFeedTrustLevel(StrEnum):
    official = "official"
    professional = "professional"
    unit_local = "unit_local"
    personal_watch = "personal_watch"
    low_trust = "low_trust"


class CustomWatchFeed(BaseModel):
    feed_id: str
    name: str
    url: HttpUrl
    category: str
    trust_level: CustomWatchFeedTrustLevel
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_refreshed_at: datetime | None = None
    last_error: str | None = None
    last_item_count: int = 0


class CreateCustomWatchFeedRequest(BaseModel):
    name: str
    url: HttpUrl
    category: str
    trust_level: CustomWatchFeedTrustLevel
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class UpdateCustomWatchFeedRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    trust_level: CustomWatchFeedTrustLevel | None = None
    enabled: bool | None = None
    tags: list[str] | None = None


class CustomWatchFeedRefreshResponse(BaseModel):
    feed: CustomWatchFeed
    records: list[MessageRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
