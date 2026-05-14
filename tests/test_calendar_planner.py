from datetime import date

from app.services.calendar.planner import DrillPrepPlanner
from app.services.calendar.providers import LocalIcsProvider


def test_drill_prep_task_generation_works() -> None:
    plan = DrillPrepPlanner().build_plan(date(2026, 6, 6), unit_id="example-1-25")

    assert plan.drill_date == date(2026, 6, 6)
    assert any(task.title.startswith("Get haircut") for task in plan.tasks)
    assert any(task.category == "travel" for task in plan.tasks)


def test_ics_export_creates_valid_calendar_content() -> None:
    plan = DrillPrepPlanner().build_plan(date(2026, 6, 6), include_travel_tasks=False)
    content = LocalIcsProvider().export_plan(plan)

    assert content.startswith("BEGIN:VCALENDAR")
    assert "VERSION:2.0" in content
    assert "BEGIN:VEVENT" in content
    assert "END:VCALENDAR" in content
    assert "DTS authorization" not in content
    assert "DTS voucher" not in content
