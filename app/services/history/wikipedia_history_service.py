from __future__ import annotations

from datetime import date

import httpx

from app.schemas.history import HistoryRefreshResponse, TodayInMarineHistoryItem
from app.services.history.local_history_store import LocalHistoryStore

_FEED_BASE = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events"

_HEADERS = {
    "User-Agent": "smcr-staff-ai/1.0 (local USMC reserve staff tool; contact via GitHub)",
    "Accept": "application/json",
}

_MILITARY_KEYWORDS = frozenset({
    # USMC-specific
    "marine", "marines", "corps", "usmc", "leatherneck",
    "iwo jima", "belleau wood", "chosin", "guadalcanal", "okinawa", "tarawa",
    # Broad military
    "battle", "war", "siege", "combat", "troops", "invasion", "assault",
    "amphibious", "landing", "naval", "navy", "army", "soldier", "military",
    "fleet", "regiment", "battalion", "division", "brigade", "squadron",
    "general", "admiral", "commander", "armed forces",
    "fort", "garrison", "liberation", "surrender", "offensive", "campaign",
    "operation", "veteran", "infantry", "artillery", "airborne",
})


class WikipediaOnThisDayService:
    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def refresh_for_date(self, target: date, store: LocalHistoryStore) -> HistoryRefreshResponse:
        warnings: list[str] = []
        fetched: list[TodayInMarineHistoryItem] = []
        try:
            raw_events, month, day = self._fetch_events(target.month, target.day)
            fetched = [item for item in (self._convert(e, month, day) for e in raw_events) if item is not None]
        except httpx.HTTPError as exc:
            warnings.append(f"Wikipedia fetch failed: {exc}. Serving cached data.")
            return HistoryRefreshResponse(
                fetched_count=0,
                imported_count=0,
                total_available=len(store.list_items()),
                date_checked=target.isoformat(),
                warnings=warnings,
            )

        stored = store.merge(fetched)
        return HistoryRefreshResponse(
            fetched_count=len(fetched),
            imported_count=len(fetched),
            total_available=len(stored),
            date_checked=target.isoformat(),
            warnings=warnings,
        )

    def _fetch_events(self, month: int, day: int) -> tuple[list[dict[str, object]], int, int]:
        url = f"{_FEED_BASE}/{month:02d}/{day:02d}"
        with httpx.Client(timeout=self.timeout_seconds, headers=_HEADERS, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        events: list[dict[str, object]] = response.json().get("events", [])
        return events, month, day

    def _convert(self, event: dict[str, object], month: int, day: int) -> TodayInMarineHistoryItem | None:
        text: str = str(event.get("text", ""))
        if not _is_military(text):
            return None
        year = str(event.get("year", ""))
        raw_pages = event.get("pages", [])
        pages: list[dict[str, object]] = raw_pages if isinstance(raw_pages, list) else []
        title = _best_title(text, pages)
        summary = text.strip()[:500]
        source_url = _source_url(pages)
        slug = _slugify(f"{month:02d}-{day:02d}-{year}-{title}")
        return TodayInMarineHistoryItem(
            slug=slug,
            title=title,
            month=month,
            day=day,
            year_label=year,
            summary=summary,
            significance=[],
            references=[source_url] if source_url else ["en.wikipedia.org"],
        )


def _is_military(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _MILITARY_KEYWORDS)


def _best_title(text: str, pages: list[dict[str, object]]) -> str:
    if pages:
        candidate = str(pages[0].get("title", "")).strip()
        if candidate and len(candidate) < 80:
            return candidate
    first_sentence = text.split(".")[0].strip()
    return first_sentence[:80] if first_sentence else text[:80]


def _source_url(pages: list[dict[str, object]]) -> str:
    if not pages:
        return ""
    content_urls = pages[0].get("content_urls", {})
    if not isinstance(content_urls, dict):
        return ""
    desktop = content_urls.get("desktop", {})
    if not isinstance(desktop, dict):
        return ""
    page = desktop.get("page", "")
    return str(page) if page else ""


def _slugify(value: str) -> str:
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")[:80]
