from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.history import TodayInMarineHistoryItem


class LocalHistoryStore:
    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.storage_dir / "today_in_history.yaml"

    def list_items(self) -> list[TodayInMarineHistoryItem]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        return [TodayInMarineHistoryItem.model_validate(item) for item in payload.get("items", [])]

    def replace(self, items: list[TodayInMarineHistoryItem]) -> list[TodayInMarineHistoryItem]:
        deduped = self._dedupe(items)
        self._write(deduped)
        return deduped

    def merge(self, items: list[TodayInMarineHistoryItem]) -> list[TodayInMarineHistoryItem]:
        merged = self._dedupe([*self.list_items(), *items])
        self._write(merged)
        return merged

    def _write(self, items: list[TodayInMarineHistoryItem]) -> None:
        payload = {"items": [item.model_dump() for item in items]}
        with open(self.path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)

    @staticmethod
    def _dedupe(items: list[TodayInMarineHistoryItem]) -> list[TodayInMarineHistoryItem]:
        seen: dict[str, TodayInMarineHistoryItem] = {}
        for item in items:
            seen[item.slug] = item
        return sorted(
            seen.values(),
            key=lambda entry: (entry.month, entry.day, entry.slug),
        )
