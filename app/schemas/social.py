from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class SocialSourceType(StrEnum):
    official = "official"
    news = "news"
    social_trend = "social_trend"
    academic = "academic"
    ngo = "ngo"
    other_public = "other_public"


class VettedSocialSource(BaseModel):
    id: str
    name: str
    source_type: SocialSourceType
    base_url: str
    allowed_collection: str
    prohibited_collection: list[str] = Field(default_factory=list)
    notes: str | None = None


class SocialTrendInput(BaseModel):
    title: str
    url: HttpUrl
    publisher: str
    source_type: SocialSourceType = SocialSourceType.social_trend
    platform: str | None = None
    author_or_channel: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    summary: str
    claim: str | None = None
    trend_signal: str | None = None
    counterargument: str | None = None
    corroborated: bool = False
    tags: list[str] = Field(default_factory=list)


class SocialTrendRecord(BaseModel):
    source_id: str
    title: str
    url: str
    publisher: str
    source_type: SocialSourceType
    platform: str | None = None
    author_or_channel: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime
    summary: str
    claim: str | None = None
    trend_signal: str | None = None
    counterargument: str | None = None
    corroborated: bool = False
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SocialIngestRequest(BaseModel):
    records: list[SocialTrendInput]
    topic: str | None = None
    strict_vetting: bool = True


class SocialIngestResponse(BaseModel):
    accepted: bool
    records_seen: int
    records_accepted: int
    records: list[SocialTrendRecord]
    osint_source_items: list[dict[str, str]]
    warnings: list[str] = Field(default_factory=list)
