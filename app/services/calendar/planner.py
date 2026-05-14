from datetime import date, timedelta
from uuid import uuid4

from app.schemas.calendar import DrillKeyEvent, DrillPrepPlanResponse, PrepTask

BASE_TASKS: tuple[tuple[str, int, str], ...] = (
    ("Confirm drill schedule, reporting location, and uniform", 14, "admin"),
    ("Check medical/dental readiness and annual training reminders", 14, "readiness"),
    ("Confirm orders or IDT lodging requirements if applicable", 10, "admin"),
    ("Submit or verify DTS authorization if travel applies", 10, "travel"),
    ("Complete required PME/training prerequisites", 7, "training"),
    ("Pack gear and inspect required uniform items", 3, "gear"),
    ("Get haircut and grooming squared away", 2, "personal"),
    ("Confirm travel plan and arrival time", 2, "travel"),
    ("Create DTS voucher reminder after drill", -2, "travel"),
)


class DrillPrepPlanner:
    def build_plan(
        self,
        drill_date: date,
        unit_id: str | None = None,
        include_travel_tasks: bool = True,
        key_events: list[DrillKeyEvent] | None = None,
        context_ids: list[str] | None = None,
        local_context_used: bool = False,
        warnings: list[str] | None = None,
    ) -> DrillPrepPlanResponse:
        tasks: list[PrepTask] = []
        for title, offset, category in BASE_TASKS:
            if not include_travel_tasks and category == "travel":
                continue
            due_date = drill_date - timedelta(days=offset) if offset >= 0 else drill_date + timedelta(days=abs(offset))
            tasks.append(
                PrepTask(
                    title=title,
                    due_offset_days=offset,
                    due_date=due_date,
                    category=category,
                )
            )
        suffix = f"-{unit_id}" if unit_id else ""
        return DrillPrepPlanResponse(
            id=f"drill-{drill_date.isoformat()}{suffix}-{uuid4().hex[:8]}",
            drill_date=drill_date,
            tasks=tasks,
            key_events=key_events or [],
            context_ids=context_ids or [],
            local_context_used=local_context_used,
            warnings=[
                "Drill prep tasks are typical/advisory and must be verified against official unit guidance.",
                "No live calendar provider is connected in this prototype.",
                *(warnings or []),
            ],
        )
