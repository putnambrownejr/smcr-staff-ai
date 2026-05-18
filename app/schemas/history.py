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
