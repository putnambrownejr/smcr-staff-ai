from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ProductTemplateType(StrEnum):
    cub_brief = "cub_brief"
    civil_preparation_battlespace = "civil_preparation_battlespace"
    cpb = "cpb"
    opord = "opord"
    warno = "warno"
    frago = "frago"
    conop = "conop"
    sitrep = "sitrep"
    aar = "aar"
    ipb = "ipb"
    decision_brief = "decision_brief"
    command_update_brief = "command_update_brief"
    naval_letter = "naval_letter"
    memorandum = "memorandum"
    endorsement = "endorsement"
    other = "other"


class ProductTemplateRecord(BaseModel):
    template_id: str
    template_name: str
    template_type: ProductTemplateType
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_context_id: str | None = None
    source_filename: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    audience_hint: str | None = None
    preferred_format: str | None = None
    reusable_headings: list[str] = Field(default_factory=list)
    reusable_guidance: list[str] = Field(default_factory=list)
    example_excerpt: str | None = None
    local_only: bool = True
    warnings: list[str] = Field(default_factory=list)


class CreateProductTemplateFromContextRequest(BaseModel):
    context_id: str = Field(min_length=16)
    template_name: str = Field(min_length=1)
    template_type: ProductTemplateType
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    audience_hint: str | None = None
    preferred_format: str | None = None
    reusable_headings: list[str] = Field(default_factory=list)
    reusable_guidance: list[str] = Field(default_factory=list)


class CreateManualProductTemplateRequest(BaseModel):
    template_name: str = Field(min_length=1)
    template_type: ProductTemplateType
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    audience_hint: str | None = None
    preferred_format: str | None = None
    reusable_headings: list[str] = Field(default_factory=list)
    reusable_guidance: list[str] = Field(default_factory=list)
    example_excerpt: str | None = None


class ProductTemplateListResponse(BaseModel):
    total_templates: int
    by_type: dict[str, int]
    records: list[ProductTemplateRecord]
