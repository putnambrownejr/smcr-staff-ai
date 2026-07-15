from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.schemas.fitreps import (
    FitrepAnalyticsResponse,
    FitrepReport,
    FitrepRsSummary,
    FitrepTrendPoint,
    FitrepWorkspace,
)


def build_fitrep_analytics(workspace: FitrepWorkspace) -> FitrepAnalyticsResponse:
    reports = sorted(workspace.reports, key=_report_sort_key)
    warnings: list[str] = []
    if not reports:
        warnings.append("No confirmed reports are available. Add or import a record to begin analysis.")
    elif len(reports) < 3:
        warnings.append("The sample is small; treat trends as descriptive observations, not stable conclusions.")

    rv_trend = [
        FitrepTrendPoint(report_id=item.report_id, label=_report_label(item), value=item.relative_value)
        for item in reports
        if item.relative_value is not None
    ]
    if reports and len(rv_trend) != len(reports):
        warnings.append("Some reports have no relative value and are omitted from the relative-value trend.")

    trait_trends: dict[str, list[FitrepTrendPoint]] = defaultdict(list)
    for report in reports:
        for trait, value in sorted(report.traits.items()):
            trait_trends[trait].append(
                FitrepTrendPoint(
                    report_id=report.report_id,
                    label=_report_label(report),
                    value=Decimal(str(value)),
                )
            )

    by_rs: dict[str, list[FitrepReport]] = defaultdict(list)
    for report in reports:
        by_rs[report.rs_label or "Unspecified RS"].append(report)
    summaries: list[FitrepRsSummary] = []
    for rs_label, rs_reports in sorted(by_rs.items()):
        rv_values = [item.relative_value for item in rs_reports if item.relative_value is not None]
        summaries.append(
            FitrepRsSummary(
                rs_label=rs_label,
                report_count=len(rs_reports),
                average_relative_value=(sum(rv_values, Decimal("0")) / len(rv_values)) if rv_values else None,
                minimum_relative_value=min(rv_values) if rv_values else None,
                maximum_relative_value=max(rv_values) if rv_values else None,
            )
        )

    distribution: dict[int, int] = defaultdict(int)
    for report in reports:
        if report.comparative_assessment is not None:
            distribution[report.comparative_assessment] += 1

    return FitrepAnalyticsResponse(
        sample_size=len(reports),
        relative_value_trend=rv_trend,
        trait_trends=dict(trait_trends),
        by_reporting_senior=summaries,
        comparative_assessment_distribution=dict(distribution),
        data_quality_warnings=warnings,
    )


def _report_sort_key(report: FitrepReport) -> tuple[str, str]:
    return (report.period_end.isoformat() if report.period_end else "9999-12-31", report.report_id)


def _report_label(report: FitrepReport) -> str:
    return report.period_end.isoformat() if report.period_end else (report.occasion or report.report_id)
