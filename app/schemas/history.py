from pydantic import BaseModel, Field


class TodayInMarineHistoryItem(BaseModel):
    slug: str
    title: str
    month: int
    day: int
    year_label: str
    summary: str
    significance: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class HistoryRefreshResponse(BaseModel):
    fetched_count: int
    imported_count: int
    total_available: int
    date_checked: str
    warnings: list[str] = Field(default_factory=list)


class HistoryImportRequest(BaseModel):
    markdown_paths: list[str] = Field(default_factory=list)
    replace_existing: bool = False


class HistoryImportResponse(BaseModel):
    imported_count: int
    total_available: int
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
