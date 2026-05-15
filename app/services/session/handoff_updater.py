from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, date, datetime

from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.handoff_updates import (
    HandoffApplyUpdateRequest,
    HandoffApplyUpdateResponse,
    HandoffDraftUpdateResponse,
    HandoffUpdateDraftRequest,
    HandoffUpdatePatch,
)
from app.schemas.session import (
    CareerTrend,
    DrillDateRecord,
    FitrepReminder,
    PmeStatus,
    RecurringCheck,
    UserSessionHandoff,
)
from app.services.session.handoff_store import SessionHandoffStore

DATE_PATTERNS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y")
LINE_SPLIT = re.compile(r"\n+")
BULLET_PREFIX = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s*")


class HandoffUpdater:
    def __init__(self, store: SessionHandoffStore) -> None:
        self.store = store

    def draft_update(self, user_key: str, request: HandoffUpdateDraftRequest) -> HandoffDraftUpdateResponse:
        existing = self.store.get(user_key)
        warnings = [*DEFAULT_WARNINGS, *detect_sensitive_input(request.notes)]
        patch = _extract_patch(request.notes)
        proposed = _merge_handoff(existing, user_key, patch)
        return HandoffDraftUpdateResponse(
            user_key=user_key,
            title=request.title or "Proposed session handoff update",
            existing_handoff=existing,
            proposed_handoff=proposed,
            patch=patch,
            warnings=warnings + ["Review this draft update before applying it to the stored handoff."],
        )

    def apply_update(self, user_key: str, request: HandoffApplyUpdateRequest) -> HandoffApplyUpdateResponse:
        existing = self.store.get(user_key)
        merged = _merge_handoff(existing, user_key, request.patch)
        saved = self.store.upsert(merged)
        return HandoffApplyUpdateResponse(
            handoff=saved,
            message="Applied confirmed draft update to the local session handoff.",
            applied_categories=_applied_categories(request.patch),
        )


def _extract_patch(notes: str) -> HandoffUpdatePatch:
    patch = HandoffUpdatePatch()
    for raw_line in LINE_SPLIT.split(notes.replace("\r\n", "\n")):
        line = _clean_line(raw_line)
        if not line:
            continue
        lowered = line.lower()
        extracted_date = _extract_date(line)
        extracted_dates = _extract_dates(line)

        if _is_pme_line(lowered):
            patch.pme.append(
                PmeStatus(
                    program=_program_name(line),
                    status=_status_name(lowered),
                    due_date=extracted_date,
                    notes=line,
                )
            )
            continue
        if "fitrep" in lowered or "fitness report" in lowered:
            patch.fitreps.append(
                FitrepReminder(
                    occasion=_fitrep_occasion(line),
                    due_date=extracted_date,
                    role=_fitrep_role(line),
                    notes=line,
                )
            )
            continue
        if _is_book_line(lowered):
            patch.recommended_books.append(line)
            continue
        if _is_course_line(lowered):
            patch.recommended_courses.append(line)
            continue
        if _is_trend_line(lowered):
            patch.career_trends.append(
                CareerTrend(
                    label=_trend_label(line),
                    direction="watch",
                    evidence=[line],
                    recommended_action="Review and confirm whether this trend should drive a concrete next step.",
                )
            )
            continue
        if _is_drill_schedule_line(lowered) and extracted_dates:
            patch.drill_dates.extend(
                DrillDateRecord(drill_date=item, label="Drill schedule") for item in extracted_dates
            )
            continue
        if _is_recurring_drill_line(lowered):
            patch.recurring_drill_notes.append(line)
            patch.recurring_checks.append(_recurring_check(line))
            if _is_admin_line(lowered):
                patch.admin_watch_items.append(line)
            continue
        if _is_preference_line(line):
            key, value = _parse_preference(line)
            if key and value:
                patch.preferences[key] = value
            continue
        if _is_recurring_check_line(lowered):
            patch.recurring_checks.append(_recurring_check(line))
            if _is_admin_line(lowered):
                patch.admin_watch_items.append(line)
            continue
        if _is_admin_line(lowered):
            patch.admin_watch_items.append(line)

    patch.pme = _unique_models(patch.pme, lambda item: f"{item.program}|{item.status}|{item.due_date}|{item.notes}")
    patch.fitreps = _unique_models(
        patch.fitreps,
        lambda item: f"{item.occasion}|{item.due_date}|{item.role}|{item.notes}",
    )
    patch.career_trends = _unique_models(
        patch.career_trends,
        lambda item: f"{item.label}|{item.direction}|{'|'.join(item.evidence)}",
    )
    patch.drill_dates = _unique_models(
        patch.drill_dates,
        lambda item: f"{item.drill_date.isoformat()}|{item.label or ''}",
    )
    patch.recurring_drill_notes = _dedupe_strings(patch.recurring_drill_notes)
    patch.recurring_checks = _unique_models(
        patch.recurring_checks,
        lambda item: f"{item.title}|{item.cadence}|{item.category}|{item.due_offset_days}|{item.notes or ''}",
    )
    patch.admin_watch_items = _dedupe_strings(patch.admin_watch_items)
    patch.recommended_books = _dedupe_strings(patch.recommended_books)
    patch.recommended_courses = _dedupe_strings(patch.recommended_courses)
    return patch


def _merge_handoff(
    existing: UserSessionHandoff | None,
    user_key: str,
    patch: HandoffUpdatePatch,
) -> UserSessionHandoff:
    base = existing.model_copy(deep=True) if existing is not None else UserSessionHandoff(user_key=user_key)
    base.user_key = user_key
    base.pme = _merge_models(base.pme, patch.pme, lambda item: f"{item.program}|{item.status}|{item.due_date}")
    base.fitreps = _merge_models(
        base.fitreps,
        patch.fitreps,
        lambda item: f"{item.occasion}|{item.due_date}|{item.role}",
    )
    base.drill_dates = _merge_models(
        base.drill_dates,
        patch.drill_dates,
        lambda item: f"{item.drill_date.isoformat()}|{item.label or ''}",
    )
    base.recurring_drill_notes = _merge_strings(base.recurring_drill_notes, patch.recurring_drill_notes)
    base.recurring_checks = _merge_models(
        base.recurring_checks,
        patch.recurring_checks,
        lambda item: f"{item.title}|{item.cadence}|{item.category}|{item.due_offset_days}",
    )
    base.admin_watch_items = _merge_strings(base.admin_watch_items, patch.admin_watch_items)
    base.career_trends = _merge_models(
        base.career_trends,
        patch.career_trends,
        lambda item: f"{item.label}|{item.direction}",
    )
    base.recommended_books = _merge_strings(base.recommended_books, patch.recommended_books)
    base.recommended_courses = _merge_strings(base.recommended_courses, patch.recommended_courses)
    base.preferences = {**base.preferences, **patch.preferences}
    base.updated_at = datetime.now(UTC)
    return base


def _applied_categories(patch: HandoffUpdatePatch) -> list[str]:
    categories: list[str] = []
    for name in (
        "pme",
        "fitreps",
        "drill_dates",
        "recurring_drill_notes",
        "recurring_checks",
        "admin_watch_items",
        "career_trends",
        "recommended_books",
        "recommended_courses",
    ):
        if getattr(patch, name):
            categories.append(name)
    if patch.preferences:
        categories.append("preferences")
    return categories


def _clean_line(line: str) -> str:
    return BULLET_PREFIX.sub("", line).strip()


def _extract_date(text: str) -> date | None:
    dates = _extract_dates(text)
    return dates[0] if dates else None


def _extract_dates(text: str) -> list[date]:
    results: list[date] = []
    tokens = re.findall(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b", text)
    for token in tokens:
        for pattern in DATE_PATTERNS:
            try:
                results.append(datetime.strptime(token, pattern).date())
                break
            except ValueError:
                continue
    return results


def _is_pme_line(lowered: str) -> bool:
    return any(token in lowered for token in ("pme", "ews", "expeditionary warfare school", "seminar", "resident"))


def _is_course_line(lowered: str) -> bool:
    return any(token in lowered for token in ("marinenet", "course", "webinar", "training module"))


def _is_book_line(lowered: str) -> bool:
    return any(token in lowered for token in ("read ", "reading list", "book:", "read:", "book recommendation"))


def _is_trend_line(lowered: str) -> bool:
    return any(token in lowered for token in ("trend", "goal", "interest", "broadening", "career aim"))


def _is_recurring_drill_line(lowered: str) -> bool:
    return "each drill" in lowered or "every drill" in lowered or "monthly drill" in lowered


def _is_drill_schedule_line(lowered: str) -> bool:
    return "drill schedule" in lowered or "drill dates" in lowered or "annual drill" in lowered


def _is_recurring_check_line(lowered: str) -> bool:
    cadence_tokens = ("monthly", "quarterly", "annually", "yearly", "before drill", "after drill")
    reminder_tokens = ("haircut", "gear", "uniform", "mypay", "tsp", "dts", "voucher", "medical", "training")
    return any(token in lowered for token in cadence_tokens) and any(token in lowered for token in reminder_tokens)


def _is_preference_line(text: str) -> bool:
    prefixes = ("preference", "pref", "location", "focus")
    return ":" in text and any(text.lower().startswith(prefix) for prefix in prefixes)


def _is_admin_line(lowered: str) -> bool:
    keywords = ("dts", "voucher", "orders", "medical", "dental", "pay", "travel", "readiness", "admin", "suspense")
    return any(
        token in lowered
        for token in keywords
    )


def _recurring_check(line: str) -> RecurringCheck:
    lowered = line.lower()
    cadence = "each_drill"
    if "monthly" in lowered:
        cadence = "monthly"
    elif "quarterly" in lowered:
        cadence = "quarterly"
    elif "annually" in lowered or "yearly" in lowered:
        cadence = "yearly"
    elif "after drill" in lowered:
        cadence = "post_drill"
    elif "before drill" in lowered:
        cadence = "pre_drill"
    elif "each drill" in lowered or "every drill" in lowered or "monthly drill" in lowered:
        cadence = "each_drill"

    category = "admin"
    if any(token in lowered for token in ("haircut", "uniform", "gear")):
        category = "readiness"
    elif any(token in lowered for token in ("dts", "voucher", "gtcc", "travel")):
        category = "travel"
    elif any(token in lowered for token in ("mypay", "tsp", "pay")):
        category = "finance"
    elif any(token in lowered for token in ("marinenet", "pme", "training")):
        category = "training"
    elif any(token in lowered for token in ("medical", "dental")):
        category = "medical"

    due_offset_days: int | None = None
    if cadence == "pre_drill":
        due_offset_days = -7
    elif cadence == "post_drill":
        due_offset_days = 3

    return RecurringCheck(
        title=line,
        cadence=cadence,
        category=category,
        due_offset_days=due_offset_days,
        notes=line,
    )


def _program_name(line: str) -> str:
    for program in ("EWSDEP", "EWS", "CSCDEP", "Command and Staff", "Expeditionary Warfare School"):
        if program.lower() in line.lower():
            return program
    return line[:80]


def _status_name(lowered: str) -> str:
    for status in ("complete", "completed", "incomplete", "enrolled", "not started", "due", "pending"):
        if status in lowered:
            return status
    return "watch"


def _fitrep_occasion(line: str) -> str:
    for occasion in ("Annual", "Change of Reporting Senior", "Transfer", "Extended"):
        if occasion.lower() in line.lower():
            return occasion
    return "FitRep watch"


def _fitrep_role(line: str) -> str | None:
    for role in ("MRO", "RS", "RO", "Reviewing Officer"):
        if role.lower() in line.lower():
            return role
    return None


def _trend_label(line: str) -> str:
    return line[:120]


def _parse_preference(line: str) -> tuple[str | None, str | None]:
    key, _, value = line.partition(":")
    normalized = key.strip().lower().replace("preference", "").replace("pref", "").strip(" -")
    if not normalized:
        normalized = "general"
    cleaned_value = value.strip()
    if "=" in cleaned_value:
        left, _, right = cleaned_value.partition("=")
        if not normalized or normalized == "general":
            normalized = left.strip().lower().replace(" ", "_")
        cleaned_value = right.strip()
    if not cleaned_value:
        return None, None
    return normalized.replace(" ", "_"), cleaned_value


def _merge_strings(existing: list[str], new: list[str]) -> list[str]:
    return _dedupe_strings([*existing, *new])


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _merge_models[T](existing: list[T], new: list[T], key_fn: Callable[[T], str]) -> list[T]:
    merged = list(existing)
    seen = {key_fn(item) for item in existing}
    for item in new:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def _unique_models[T](items: list[T], key_fn: Callable[[T], str]) -> list[T]:
    result: list[T] = []
    seen: set[str] = set()
    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
