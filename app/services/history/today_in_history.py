from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from app.schemas.history import TodayInMarineHistoryItem


class TodayInMarineHistoryService:
    def __init__(self, items: list[TodayInMarineHistoryItem]) -> None:
        self.items = items

    @classmethod
    def from_yaml(cls, path: str | Path) -> TodayInMarineHistoryService:
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        items = [TodayInMarineHistoryItem.model_validate(item) for item in payload.get("items", [])]
        return cls(items)

    def get_for_date(self, target_date: date) -> list[TodayInMarineHistoryItem]:
        return [
            item
            for item in self.items
            if item.month == target_date.month and item.day == target_date.day
        ]
