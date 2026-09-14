from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

DRAFT_NOTICE = "DRAFT — Verify all references against current official sources before acting."
Category = Literal["reference", "template", "prompt_pack"]


class SourceLink(BaseModel):
    title: str
    url: str

    @field_validator("url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Source links must be public HTTPS URLs without credentials.")
        return value


class LibraryItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")
    title: str
    category: Category
    summary: str
    content: str
    sources: list[SourceLink]
    source_file: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification_status: Literal["not_live_verified"] = "not_live_verified"
    last_verified_at: None = None
    notice: str = DRAFT_NOTICE


class SearchItem(BaseModel):
    id: str
    title: str
    category: Category
    summary: str
    sources: list[SourceLink]
    verification_status: str
    last_verified_at: None = None


class SearchResults(BaseModel):
    items: list[SearchItem]
    total: int
    offset: int
    next_offset: int | None
    notice: str = DRAFT_NOTICE


class CatalogSnapshot(BaseModel):
    schema_version: Literal[1] = 1
    items: list[LibraryItem]
