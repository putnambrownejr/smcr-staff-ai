from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.schemas.sources import ManifestValidationResult


class DocumentRead(BaseModel):
    source_id: str
    title: str
    publication_type: str
    issuing_org: str | None = None
    url: str | None = None
    retrieved_at: datetime
    version: str | None = None
    effective_date: datetime | None = None
    classification_label: str = "UNCLASSIFIED"
    cui_flag: bool = False
    source_hash: str | None = None


class IngestRequest(BaseModel):
    source_type: str = Field(pattern="^(manifest|rss|pdf|html)$")
    url: HttpUrl | None = None
    local_path: str | None = None
    dry_run: bool = True

    @model_validator(mode="after")
    def require_exactly_one_source(self) -> Self:
        if bool(self.url) == bool(self.local_path):
            raise ValueError("Provide exactly one of url or local_path.")
        if self.source_type in {"rss", "html"} and self.local_path:
            raise ValueError("rss/html ingestion requires url.")
        if self.source_type in {"manifest", "pdf"} and self.url:
            raise ValueError("manifest/pdf ingestion currently requires local_path.")
        return self


class IngestResponse(BaseModel):
    accepted: bool
    message: str
    documents_seen: int = 0
    manifest_validation: ManifestValidationResult | None = None
