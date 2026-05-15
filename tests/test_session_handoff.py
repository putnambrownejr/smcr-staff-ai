from datetime import date
from pathlib import Path

from app.schemas.session import DrillDateRecord, FitrepReminder, PmeStatus, RecurringCheck, UserSessionHandoff
from app.services.session.handoff_store import SessionHandoffStore


def test_session_handoff_store_round_trip(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    handoff = UserSessionHandoff(
        user_key="capt-example",
        rank="Capt",
        mos="0602",
        pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 9, 30))],
        fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 30), role="MRO")],
        drill_dates=[DrillDateRecord(drill_date=date(2026, 6, 6), label="June drill")],
        recurring_checks=[RecurringCheck(title="Every drill review haircut and uniform.", category="readiness")],
        admin_watch_items=["DTS voucher after drill"],
    )

    saved = store.upsert(handoff)
    loaded = store.get("capt-example")

    assert loaded is not None
    assert loaded.user_key == saved.user_key
    assert loaded.pme[0].program == "EWSDEP"
    assert loaded.fitreps[0].occasion == "Annual"
    assert loaded.drill_dates[0].label == "June drill"
    assert loaded.recurring_checks[0].category == "readiness"


def test_session_handoff_store_rejects_invalid_keys(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    handoff = UserSessionHandoff(user_key="../bad")

    try:
        store.upsert(handoff)
    except ValueError:
        assert True
    else:
        raise AssertionError("Expected invalid user_key to raise ValueError")


def test_session_handoff_store_avoids_filename_collisions(tmp_path: Path) -> None:
    store = SessionHandoffStore(tmp_path)
    first = UserSessionHandoff(user_key="a.b")
    second = UserSessionHandoff(user_key="a_b")

    store.upsert(first)
    store.upsert(second)

    assert store.get("a.b") is not None
    assert store.get("a_b") is not None
    assert len(list(tmp_path.glob("*.json"))) == 2
