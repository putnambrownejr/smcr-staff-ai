from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.schemas.fitreps import (
    FitrepImportKind,
    FitrepImportProposal,
    FitrepReportCreateRequest,
    FitrepSourceType,
    RsProfileSnapshotCreateRequest,
)

_LABEL_LINE = re.compile(r"^\s*([^:\n]{2,50})\s*:\s*(.*?)\s*$", re.MULTILINE)
_TRAIT_NAMES = {"mission", "individual", "leadership", "intellect", "fitness", "character"}


def propose_report_import(text: str, context_id: str, user_key: str) -> FitrepImportProposal:
    values = _labels(text)
    warnings: list[str] = []
    traits: dict[str, float] = {}
    for name in _TRAIT_NAMES:
        parsed = _float(values.get(name))
        if parsed is not None:
            traits[name] = parsed
    relative_value = _decimal(_first(values, "relative value", "rv"))
    period_end = _date(_first(values, "reporting period end", "period end", "to date"))
    if relative_value is None:
        warnings.append("No labeled relative value was found; it was left blank for review.")
    if not values:
        warnings.append("No recognized labeled fields were found; review the source and enter values manually.")
    report = FitrepReportCreateRequest(
        user_key=user_key,
        period_end=period_end,
        occasion=_first(values, "occasion") or "",
        grade=_first(values, "grade", "rank") or "",
        billet=_first(values, "billet") or "",
        unit=_first(values, "unit") or "",
        rs_label=_first(values, "reporting senior", "rs") or "",
        ro_label=_first(values, "reviewing officer", "ro") or "",
        relative_value=relative_value,
        cumulative_relative_value=_decimal(_first(values, "cumulative relative value", "cumulative rv")),
        comparative_assessment=_int(_first(values, "comparative assessment"), minimum=1, maximum=8),
        traits=traits,
        source_type=FitrepSourceType.my_record_import,
        source_context_id=context_id,
        uncertainty_notes=list(warnings),
    )
    return FitrepImportProposal(
        kind=FitrepImportKind.my_record,
        report=report,
        warnings=warnings,
    )


def propose_rs_profile_import(text: str, context_id: str, user_key: str) -> FitrepImportProposal:
    values = _labels(text)
    warnings: list[str] = []
    rs_label = _first(values, "reporting senior", "rs") or ""
    if not rs_label:
        warnings.append("No labeled Reporting Senior was found; identify the profile before saving.")
    profile = RsProfileSnapshotCreateRequest(
        user_key=user_key,
        rs_label=rs_label,
        as_of_date=_date(_first(values, "as of", "profile date")),
        grade=_first(values, "grade", "rank") or "",
        population_size=_int(_first(values, "population", "population size"), minimum=0),
        report_count=_int(_first(values, "reports", "report count"), minimum=0),
        relative_value_average=_decimal(_first(values, "average relative value", "average rv")),
        source_type=FitrepSourceType.rs_profile_import,
        source_context_id=context_id,
        uncertainty_notes=list(warnings),
    )
    return FitrepImportProposal(
        kind=FitrepImportKind.rs_profile,
        rs_profile=profile,
        warnings=warnings,
    )


def _labels(text: str) -> dict[str, str]:
    return {match.group(1).strip().lower(): match.group(2).strip() for match in _LABEL_LINE.finditer(text)}


def _first(values: dict[str, str], *names: str) -> str | None:
    return next((values[name] for name in names if values.get(name)), None)


def _decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value.replace("%", "").strip())
    except InvalidOperation:
        return None


def _float(value: str | None) -> float | None:
    decimal = _decimal(value)
    return float(decimal) if decimal is not None else None


def _int(value: str | None, *, minimum: int, maximum: int | None = None) -> int | None:
    decimal = _decimal(value)
    if decimal is None or decimal != decimal.to_integral_value():
        return None
    parsed = int(decimal)
    if parsed < minimum or (maximum is not None and parsed > maximum):
        return None
    return parsed


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None
