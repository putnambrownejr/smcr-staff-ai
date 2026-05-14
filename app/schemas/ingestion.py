from datetime import UTC, datetime

from pydantic import BaseModel, Field


class MessageRecord(BaseModel):
    source_id: str
    title: str
    canonical_url: str
    message_number: str | None = None
    fiscal_year: int | None = None
    published_at: datetime | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_family: str = "MARADMIN"
    status: str = "current_unknown"
    source_hash: str | None = None
    parser_warnings: list[str] = Field(default_factory=list)


class PublicationRecord(BaseModel):
    source_id: str
    title: str
    canonical_url: str
    publication_number: str | None = None
    source_family: str = "MCPEL"
    issuing_org: str | None = None
    status: str = "current_unknown"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_hash: str | None = None
    parser_warnings: list[str] = Field(default_factory=list)
