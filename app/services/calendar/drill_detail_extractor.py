import re
from datetime import date, datetime, time

from app.core.security import detect_sensitive_input
from app.schemas.calendar import DrillKeyEvent

DATE_PATTERN = re.compile(r"\b(?P<date>\d{4}-\d{2}-\d{2})\b")
TIME_PATTERN = re.compile(r"\b(?P<time>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?\b", re.IGNORECASE)


def extract_drill_details(
    text: str,
    *,
    source_context_id: str,
    default_date: date,
) -> list[DrillKeyEvent]:
    """Extract simple user-provided drill details from local text.

    This is deliberately conservative. It supports lightweight templates such as:
    `Event: Check-in | Date: 2026-06-05 | Time: 1800 | Location: Reserve Center | Due: CAC, orders`.
    """

    events: list[DrillKeyEvent] = []
    warnings = detect_sensitive_input(text)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or not _looks_like_event(line):
            continue
        title = _field(line, "event") or _field(line, "title") or line.split("|", maxsplit=1)[0].strip()
        event_date = _parse_date(_field(line, "date") or line) or default_date
        start_time = _parse_time(_field(line, "time") or _field(line, "start") or "")
        location = _field(line, "location")
        uniform = _field(line, "uniform")
        due_raw = _field(line, "due") or _field(line, "due_outs") or ""
        due_outs = [item.strip() for item in re.split(r"[,;]", due_raw) if item.strip()]
        events.append(
            DrillKeyEvent(
                title=title[:120],
                event_date=event_date,
                start_time=start_time,
                location=location,
                uniform=uniform,
                due_outs=due_outs,
                source_context_id=source_context_id,
                confidence="low",
                notes="Extracted from user-uploaded local context; verify before use.",
                warnings=warnings,
            )
        )
    return events[:20]


def _looks_like_event(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in ("event:", "title:", "time:", "location:", "due:", "uniform:"))


def _field(line: str, name: str) -> str | None:
    pattern = re.compile(rf"(?:^|\|)\s*{re.escape(name)}\s*:\s*([^|]+)", re.IGNORECASE)
    match = pattern.search(line)
    return match.group(1).strip() if match else None


def _parse_date(value: str) -> date | None:
    match = DATE_PATTERN.search(value)
    if match is None:
        return None
    return date.fromisoformat(match.group("date"))


def _parse_time(value: str) -> time | None:
    match = TIME_PATTERN.search(value)
    if match is None:
        return None
    hour = int(match.group("time"))
    minute = int(match.group("minute") or "0")
    ampm = (match.group("ampm") or "").lower()
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    return datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()
