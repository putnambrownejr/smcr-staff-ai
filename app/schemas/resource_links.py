from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ResourceLinkCategory(StrEnum):
    admin_pay = "admin_pay"
    training_pme = "training_pme"
    news_info = "news_info"
    benefits = "benefits"
    comms = "comms"
    reserve = "reserve"
    reference = "reference"
    unit = "unit"


CATEGORY_LABELS: dict[ResourceLinkCategory, str] = {
    ResourceLinkCategory.admin_pay: "Admin & pay",
    ResourceLinkCategory.training_pme: "Training & PME",
    ResourceLinkCategory.news_info: "News & info",
    ResourceLinkCategory.benefits: "Benefits",
    ResourceLinkCategory.comms: "Communications",
    ResourceLinkCategory.reserve: "Reserve affairs",
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


class ResourceLinkCreate(BaseModel):
    title: str
    url: str
    category: ResourceLinkCategory = ResourceLinkCategory.unit
    description: str | None = None
    tags: list[str] = []


class ResourceLinksResponse(BaseModel):
    links: list[ResourceLink]
    total: int
    categories: dict[str, str]
