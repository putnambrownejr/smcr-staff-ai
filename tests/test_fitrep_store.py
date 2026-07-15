from datetime import date
from decimal import Decimal
from pathlib import Path

from app.schemas.fitreps import (
    FitrepImprovementGoalRequest,
    FitrepReportCreateRequest,
    RsProfileSnapshotCreateRequest,
)
from app.services.fitreps.store import FitrepStore


def test_fitrep_store_keeps_reports_rs_snapshots_and_goals_per_user(tmp_path: Path) -> None:
    store = FitrepStore(tmp_path / "fitreps")
    report = store.add_report(
        FitrepReportCreateRequest(
            user_key="capt-fitrep",
            period_end=date(2026, 6, 30),
            occasion="AN",
            grade="Capt",
            billet="S-4",
            rs_label="RS Alpha",
            relative_value=Decimal("92.4"),
            traits={"leadership": 5.0, "mission": 4.5},
        )
    )
    first = store.add_rs_snapshot(
        RsProfileSnapshotCreateRequest(
            user_key="capt-fitrep",
            rs_label="RS Alpha",
            as_of_date=date(2026, 6, 30),
            grade="Capt",
            population_size=8,
            report_count=12,
        )
    )
    second = store.add_rs_snapshot(
        RsProfileSnapshotCreateRequest(
            user_key="capt-fitrep",
            rs_label="RS Alpha",
            as_of_date=date(2026, 7, 31),
            grade="Capt",
            population_size=9,
            report_count=13,
        )
    )
    goal = store.upsert_goal(
        FitrepImprovementGoalRequest(
            user_key="capt-fitrep",
            rs_label="RS Alpha",
            title="Increase observed planning leadership",
            evidence=["Lead the next two planning sessions"],
        )
    )

    workspace = store.get("capt-fitrep")
    assert workspace.reports == [report]
    assert [item.snapshot_id for item in workspace.rs_profiles] == [first.snapshot_id, second.snapshot_id]
    assert workspace.goals == [goal]
    assert store.get("other-user").reports == []


def test_fitrep_store_updates_and_deletes_report(tmp_path: Path) -> None:
    store = FitrepStore(tmp_path / "fitreps")
    report = store.add_report(FitrepReportCreateRequest(user_key="capt-fitrep", occasion="AN"))
    updated = store.update_report(
        "capt-fitrep",
        report.report_id,
        FitrepReportCreateRequest(user_key="capt-fitrep", occasion="TR", billet="OpsO"),
    )
    assert updated.occasion == "TR"
    assert updated.billet == "OpsO"
    assert store.delete_report("capt-fitrep", report.report_id) is True
    assert store.get("capt-fitrep").reports == []
