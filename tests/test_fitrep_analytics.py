from datetime import date
from decimal import Decimal

from app.schemas.fitreps import FitrepReport, FitrepWorkspace
from app.services.fitreps.analytics import build_fitrep_analytics


def test_fitrep_analytics_builds_transparent_trends_and_rs_groups() -> None:
    reports = [
        FitrepReport(
            report_id="r1",
            user_key="capt-fitrep",
            period_end=date(2025, 6, 30),
            rs_label="RS Alpha",
            relative_value=Decimal("88.0"),
            comparative_assessment=4,
            traits={"leadership": 4.0},
        ),
        FitrepReport(
            report_id="r2",
            user_key="capt-fitrep",
            period_end=date(2026, 6, 30),
            rs_label="RS Alpha",
            relative_value=Decimal("92.0"),
            comparative_assessment=3,
            traits={"leadership": 5.0},
        ),
    ]
    analytics = build_fitrep_analytics(FitrepWorkspace(user_key="capt-fitrep", reports=reports))
    assert [point.value for point in analytics.relative_value_trend] == [Decimal("88.0"), Decimal("92.0")]
    assert analytics.by_reporting_senior[0].average_relative_value == Decimal("90.0")
    assert analytics.trait_trends["leadership"][1].value == Decimal("5.0")
    assert analytics.sample_size == 2
    assert any("small" in warning.lower() for warning in analytics.data_quality_warnings)


def test_fitrep_analytics_handles_empty_workspace() -> None:
    analytics = build_fitrep_analytics(FitrepWorkspace(user_key="capt-fitrep"))
    assert analytics.sample_size == 0
    assert analytics.relative_value_trend == []
    assert analytics.data_quality_warnings
