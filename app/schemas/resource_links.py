from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlsplit

from pydantic import BaseModel, field_validator


def _validate_http_url(value: str) -> str:
    candidate = value.strip()
    if not candidate or any(character.isspace() for character in candidate):
        raise ValueError("URL must be a valid http:// or https:// address.")
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("URL must be a valid http:// or https:// address.") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname:
        raise ValueError("URL must be a valid http:// or https:// address.")
    return candidate


class ResourceLinkCategory(StrEnum):
    usmc_official = "usmc_official"
    admin_pay = "admin_pay"
    training_pme = "training_pme"
    news_info = "news_info"
    benefits = "benefits"
    comms = "comms"
    reserve = "reserve"
    it_access = "it_access"
    reference = "reference"
    unit = "unit"


CATEGORY_LABELS: dict[ResourceLinkCategory, str] = {
    ResourceLinkCategory.usmc_official: "USMC official",
    ResourceLinkCategory.admin_pay: "Admin & pay",
    ResourceLinkCategory.training_pme: "Training & PME",
    ResourceLinkCategory.news_info: "News & info",
    ResourceLinkCategory.benefits: "Benefits",
    ResourceLinkCategory.comms: "Communications",
    ResourceLinkCategory.reserve: "Reserve affairs",
    ResourceLinkCategory.it_access: "IT & access",
    ResourceLinkCategory.reference: "Reference",
    ResourceLinkCategory.unit: "Unit-specific",
}


class ResourceLink(BaseModel):
    id: str
    title: str
    url: str
    category: ResourceLinkCategory
    description: str | None = None
    is_seed: bool = True
    tags: list[str] = []

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_http_url(value)


class ResourceLinkCreate(BaseModel):
    title: str
    url: str
    category: ResourceLinkCategory = ResourceLinkCategory.unit
    description: str | None = None
    tags: list[str] = []

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_http_url(value)


class ResourceLinksResponse(BaseModel):
    links: list[ResourceLink]
    total: int
    categories: dict[str, str]
