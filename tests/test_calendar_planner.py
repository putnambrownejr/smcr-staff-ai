from datetime import date

from app.schemas.session import RecurringCheck
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


def test_drill_prep_plan_includes_recurring_checks() -> None:
    plan = DrillPrepPlanner().build_plan(
        date(2026, 6, 6),
        recurring_checks=[
            RecurringCheck(
                title="After drill review DTS voucher and close travel-admin loose ends.",
                cadence="post_drill",
                category="travel",
                due_offset_days=3,
            ),
            RecurringCheck(
                title="Monthly review myPay and TSP allocations.",
                cadence="monthly",
                category="finance",
            ),
        ],
        recurring_drill_notes=["Every drill confirm uniform and haircut."],
    )

    titles = {task.title for task in plan.tasks}
    assert "After drill review DTS voucher and close travel-admin loose ends." in titles
    assert "Monthly review myPay and TSP allocations." in titles
    assert "Every drill confirm uniform and haircut." in titles
