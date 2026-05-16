from datetime import date, timedelta
from uuid import uuid4

from app.schemas.calendar import DrillKeyEvent, DrillPrepPlanResponse, PrepTask
from app.schemas.session import RecurringCheck

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
        recurring_checks: list[RecurringCheck] | None = None,
        recurring_drill_notes: list[str] | None = None,
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
        for item in recurring_checks or []:
            if not include_travel_tasks and item.category == "travel":
                continue
            due_offset = item.due_offset_days if item.due_offset_days is not None else _default_offset(item)
            due_date = (
                drill_date - timedelta(days=due_offset)
                if due_offset >= 0
                else drill_date + timedelta(days=abs(due_offset))
            )
            tasks.append(
                PrepTask(
                    title=item.title,
                    due_offset_days=due_offset,
                    due_date=due_date,
                    category=item.category,
                )
            )
        for note in recurring_drill_notes or []:
            tasks.append(
                PrepTask(
                    title=note,
                    due_offset_days=7,
                    due_date=drill_date - timedelta(days=7),
                    category="drill_rhythm",
                )
            )
        suffix = f"-{unit_id}" if unit_id else ""
        return DrillPrepPlanResponse(
            id=f"drill-{drill_date.isoformat()}{suffix}-{uuid4().hex[:8]}",
            drill_date=drill_date,
            tasks=_dedupe_tasks(tasks),
            key_events=key_events or [],
            context_ids=context_ids or [],
            local_context_used=local_context_used,
            warnings=[
                "Drill prep tasks are typical/advisory and must be verified against official unit guidance.",
                "No live calendar provider is connected in this prototype.",
                *(warnings or []),
            ],
        )


def _default_offset(item: RecurringCheck) -> int:
    if item.cadence == "post_drill":
        return -3
    if item.cadence == "pre_drill":
        return 7
    if item.cadence == "each_drill":
        return 7
    return 14


def _dedupe_tasks(tasks: list[PrepTask]) -> list[PrepTask]:
    seen: set[str] = set()
    result: list[PrepTask] = []
    for task in sorted(tasks, key=lambda item: (item.due_date, item.title.lower())):
        key = f"{task.title.lower()}|{task.due_date.isoformat()}|{task.category.lower()}"
        if key in seen:
            continue
        seen.add(key)
        result.append(task)
    return result
