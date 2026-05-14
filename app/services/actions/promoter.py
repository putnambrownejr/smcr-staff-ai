from __future__ import annotations

import re
from datetime import date, datetime

from app.schemas.actions import (
    ActionCategory,
    ActionItemRequest,
    ActionPriority,
    ActionPromoteItemRequest,
    ActionPromoteRequest,
)

DATE_PATTERNS = [
    re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b"),
    re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b"),
]


class ActionPromoter:
    def build(self, request: ActionPromoteRequest) -> list[ActionItemRequest]:
        return [
            self._build_item(item, request)
            for item in request.items
        ]

    def _build_item(self, item: ActionPromoteItemRequest, request: ActionPromoteRequest) -> ActionItemRequest:
        category = item.category or _infer_category(item.text, request.default_category)
        priority = item.priority or _infer_priority(item.text, request.default_priority)
        suspense_date = item.suspense_date or _infer_date(item.text)
        source_ref = item.source_ref or request.source_ref
        notes = item.notes
        if suspense_date and notes is None:
            notes = "Suspense inferred from source text; verify before use."
        return ActionItemRequest(
            user_key=request.user_key,
            title=_title_from_text(item.text),
            description=item.text,
            owner=item.owner or request.default_owner,
            category=category,
            priority=priority,
            suspense_date=suspense_date,
            source_ref=source_ref,
            notes=notes,
        )


def _title_from_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip(" -")
    if len(cleaned) <= 72:
        return cleaned
    return cleaned[:69].rstrip() + "..."


def _infer_category(text: str, fallback: ActionCategory) -> ActionCategory:
    lowered = text.lower()
    if any(token in lowered for token in ("dts", "travel", "lodging", "voucher", "itinerary")):
        return ActionCategory.travel
    if any(token in lowered for token in ("fitrep", "pes", "reporting senior", "rs", "ro")):
        return ActionCategory.fitrep
    if any(token in lowered for token in ("pme", "marinenet", "reading", "course")):
        return ActionCategory.pme
    if any(token in lowered for token in ("orders", "bio", "rqs", "document", "upload", "citation")):
        return ActionCategory.documents
    if any(
        token in lowered for token in ("range", "rso", "ammo", "training", "aar", "exercise", "at ")
    ) or lowered.startswith("at "):
        return ActionCategory.training
    if any(token in lowered for token in ("medical", "dental", "readiness", "vacc", "pha")):
        return ActionCategory.readiness
    if any(token in lowered for token in ("billet", "ados", "opportunity", "board", "career")):
        return ActionCategory.career
    if any(token in lowered for token in ("drill", "muster", "uniform", "haircut", "gear")):
        return ActionCategory.drill
    if any(token in lowered for token in ("admin", "routing", "endorsement", "package")):
        return ActionCategory.admin
    return fallback


def _infer_priority(text: str, fallback: ActionPriority) -> ActionPriority:
    lowered = text.lower()
    if any(token in lowered for token in ("urgent", "asap", "immediately", "today", "nlt", "no later than", "due")):
        return ActionPriority.high
    if any(token in lowered for token in ("this week", "soon", "confirm", "submit", "review")):
        return ActionPriority.medium
    return fallback


def _infer_date(text: str) -> date | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            return date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        except ValueError:
            return None
    try:
        parsed = datetime.strptime(text, "%m/%d/%Y")
        return parsed.date()
    except ValueError:
        return None
