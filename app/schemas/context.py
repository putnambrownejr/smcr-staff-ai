from datetime import date, datetime

from pydantic import BaseModel, Field


class LocalContextMetadata(BaseModel):
    context_id: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime
    tags: list[str] = Field(default_factory=list)
    document_type: str = "other"
    contains_pii: bool = False
    retention_policy: str = "user_managed_local"
    consent_ack: bool = False
    review_date: date | None = None
    expiration_date: date | None = None
    advisory_only: bool = True
    affects_canonical_structure: bool = False
    warnings: list[str] = Field(default_factory=list)


class LocalContextListResponse(BaseModel):
    items: list[LocalContextMetadata]


class LocalContextUploadResponse(BaseModel):
    item: LocalContextMetadata
    message: str


class LocalContextReadResponse(BaseModel):
    item: LocalContextMetadata
    text_preview: str
