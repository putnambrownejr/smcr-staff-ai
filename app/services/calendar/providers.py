from abc import ABC, abstractmethod
from datetime import UTC, datetime, time

from app.schemas.calendar import DrillPrepPlanResponse


class CalendarProvider(ABC):
    @abstractmethod
    def export_plan(self, plan: DrillPrepPlanResponse) -> str:
        raise NotImplementedError


class LocalIcsProvider(CalendarProvider):
    def export_plan(self, plan: DrillPrepPlanResponse) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//smcr-staff-ai//drill-prep//EN",
        ]
        for task in plan.tasks:
            due_dt = datetime.combine(task.due_date, time(hour=9))
            uid = f"{plan.id}-{task.category}-{task.due_date.isoformat()}@smcr-staff-ai"
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{due_dt.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{_escape_ics(task.title)}",
                    "DESCRIPTION:Advisory SMCR drill-prep reminder. Verify with official guidance.",
                    "END:VEVENT",
                ]
            )
        for event in plan.key_events:
            start_hour = event.start_time.hour if event.start_time else 9
            start_minute = event.start_time.minute if event.start_time else 0
            start_dt = datetime.combine(event.event_date, time(hour=start_hour, minute=start_minute))
            uid = f"{plan.id}-event-{event.event_date.isoformat()}-{_escape_ics(event.title)}@smcr-staff-ai"
            description = "; ".join(event.due_outs) or (
                "User-provided drill key event. Verify classification and guidance."
            )
            end_lines = []
            if event.end_time:
                end_dt = datetime.combine(event.event_date, event.end_time)
                end_lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}")
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                    *end_lines,
                    f"SUMMARY:{_escape_ics(event.title)}",
                    *([f"LOCATION:{_escape_ics(event.location)}"] if event.location else []),
                    f"DESCRIPTION:{_escape_ics(description)}",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"


def _escape_ics(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
