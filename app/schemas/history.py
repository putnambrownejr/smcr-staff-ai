from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class HistoryScope(StrEnum):
    usmc = "usmc"
    us_military = "us_military"


class TodayInMarineHistoryItem(BaseModel):
    slug: str
    title: str
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    year_label: str
    summary: str
    # Legacy local records predate scope metadata. The old feature and its
    # importer were explicitly Marine-history-only, so USMC is the safe
    # backward-compatible interpretation for those records.
    scope: HistoryScope = HistoryScope.usmc
    significance: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_calendar_date(self) -> Self:
        date(2000, self.month, self.day)
        return self


class HistorySelection(BaseModel):
    item: TodayInMarineHistoryItem
    is_exact: bool
    distance_days: int


class HistoryRefreshResponse(BaseModel):
    fetched_count: int
    imported_count: int
    total_available: int
    date_checked: str
    warnings: list[str] = Field(default_factory=list)


class HistoryImportRequest(BaseModel):
    markdown_paths: list[str] = Field(default_factory=list)
    replace_existing: bool = False
    scope: HistoryScope = HistoryScope.usmc


class HistoryImportResponse(BaseModel):
    imported_count: int
    total_available: int
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
