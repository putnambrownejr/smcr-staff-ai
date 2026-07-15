from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.schemas.history import HistoryScope, HistorySelection, TodayInMarineHistoryItem

_REFERENCE_YEAR = 2000
_DAYS_IN_REFERENCE_YEAR = 366


def _calendar_index(month: int, day: int) -> int:
    return date(_REFERENCE_YEAR, month, day).timetuple().tm_yday - 1


class TodayInMarineHistoryService:
    def __init__(self, items: list[TodayInMarineHistoryItem]) -> None:
        self.items = items

    @classmethod
    def from_yaml(cls, path: str | Path) -> TodayInMarineHistoryService:
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        items = [TodayInMarineHistoryItem.model_validate(item) for item in payload.get("items", [])]
        return cls(items)

    @classmethod
    def from_paths(cls, paths: list[str | Path]) -> TodayInMarineHistoryService:
        items: list[TodayInMarineHistoryItem] = []
        seen: set[str] = set()
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            try:
                with open(path, encoding="utf-8") as handle:
                    payload = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError):
                continue
            if not isinstance(payload, dict):
                continue
            for item_payload in payload.get("items", []):
                try:
                    item = TodayInMarineHistoryItem.model_validate(item_payload)
                except ValidationError:
                    continue
                if item.slug in seen:
                    continue
                seen.add(item.slug)
                items.append(item)
        return cls(items)

    def get_for_date(self, target_date: date) -> list[TodayInMarineHistoryItem]:
        return [
            item
            for item in self.items
            if item.month == target_date.month and item.day == target_date.day
        ]

    def get_or_random(self, target_date: date) -> list[TodayInMarineHistoryItem]:
        items_for_date = self.get_for_date(target_date)
        if items_for_date:
            return items_for_date
        if not self.items:
            return []
        index = (target_date.month * 31 + target_date.day) % len(self.items)
        return [self.items[index]]

    def select_for_date(
        self,
        target_date: date,
        scope: HistoryScope,
    ) -> HistorySelection | None:
        candidates = [item for item in self.items if item.scope is scope]
        if not candidates:
            return None
        target_index = _calendar_index(target_date.month, target_date.day)

        def selection_key(item: TodayInMarineHistoryItem) -> tuple[int, bool, str, str]:
            item_index = _calendar_index(item.month, item.day)
            backward = (target_index - item_index) % _DAYS_IN_REFERENCE_YEAR
            forward = (item_index - target_index) % _DAYS_IN_REFERENCE_YEAR
            distance = min(backward, forward)
            # False sorts before True, so equal-distance ties prefer the
            # preceding occurrence rather than a future occurrence.
            is_following = forward < backward
            return distance, is_following, item.year_label, item.slug

        selected = min(candidates, key=selection_key)
        distance_days = selection_key(selected)[0]
        return HistorySelection(
            item=selected,
            is_exact=distance_days == 0,
            distance_days=distance_days,
        )

    def list_items(self) -> list[TodayInMarineHistoryItem]:
        return sorted(
            self.items,
            key=lambda item: (item.month, item.day, item.year_label, item.slug),
        )


_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_PRIMARY_DATE_PATTERN = re.compile(
    r"^\s*-\s+\*\*(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\s*[–-]\s*(?P<title>[^:*]+?)(?::|\*\*)"
)
_ALT_DATE_PATTERN = re.compile(
    r"^\s*-\s+\*\*(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\*\*\s*[–-]\s+\*(?P<title>[^*]+)\*"
)


def extract_history_items_from_markdown(
    markdown: str,
    source_label: str,
    scope: HistoryScope = HistoryScope.usmc,
) -> list[TodayInMarineHistoryItem]:
    items: list[TodayInMarineHistoryItem] = []
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        match = _PRIMARY_DATE_PATTERN.match(line) or _ALT_DATE_PATTERN.match(line)
        if not match:
            continue
        month = _MONTHS.get(match.group("month").lower())
        if month is None:
            continue
        day = int(match.group("day"))
        year = match.group("year")
        title = _clean_inline_text(match.group("title"))
        summary = _extract_summary(line, lines, index)
        if not summary:
            continue
        slug = _slugify(f"{month:02d}-{day:02d}-{year}-{title}")
        items.append(
            TodayInMarineHistoryItem(
                slug=slug,
                title=title,
                month=month,
                day=day,
                year_label=year,
                summary=summary,
                scope=scope,
                significance=[],
                references=[source_label],
            )
        )
    deduped: dict[str, TodayInMarineHistoryItem] = {}
    for item in items:
        deduped[item.slug] = item
    return list(deduped.values())


def _extract_summary(current_line: str, lines: list[str], index: int) -> str:
    remainder = current_line
    for marker in (":", "–", "-"):
        if marker in remainder:
            remainder = remainder.split(marker, 1)[1]
            break
    summary_parts = [_clean_inline_text(remainder)]
    follow_index = index + 1
    while follow_index < len(lines):
        next_line = lines[follow_index].strip()
        if not next_line or next_line.startswith("- **") or next_line.startswith("## "):
            break
        if next_line.startswith("- ") or next_line.startswith("|") or next_line.startswith("```"):
            break
        summary_parts.append(_clean_inline_text(next_line))
        if len(" ".join(summary_parts)) > 420:
            break
        follow_index += 1
    summary = " ".join(part for part in summary_parts if part).strip()
    return summary[:500]


def _clean_inline_text(value: str) -> str:
    cleaned = value.replace("**", "").replace("*", "").replace("`", "").strip()
    cleaned = re.sub(r"\[[^\]]+\]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -:")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")
