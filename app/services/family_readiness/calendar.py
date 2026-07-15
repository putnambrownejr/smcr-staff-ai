from datetime import UTC, datetime

from app.schemas.family_readiness import FamilyReadinessEvent


class FamilyReadinessIcsProvider:
    def export(self, event: FamilyReadinessEvent) -> str:
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//smcr-staff-ai//family-readiness//EN",
        ]
        for milestone in event.milestones:
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{event.event_id}-{milestone.milestone_id}@smcr-staff-ai",
                    f"DTSTAMP:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART;VALUE=DATE:{milestone.target_date:%Y%m%d}",
                    f"SUMMARY:{_escape_ics(milestone.title)}",
                    "DESCRIPTION:DRAFT — Verify all references against current official sources before acting.",
                    "END:VEVENT",
                ]
            )
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"


def _escape_ics(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
