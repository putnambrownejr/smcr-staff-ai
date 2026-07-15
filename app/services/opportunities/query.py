from collections.abc import Sequence

from app.schemas.career_opportunities import (
    CareerOpportunitySortField,
    OpportunityQuery,
    SortDirection,
)
from app.schemas.opportunities import OpportunityRecord
from app.services.billets.recommender import RANK_EQUIVALENTS

GRADE_ORDER = {
    alias.replace(" ", "").replace("-", ""): index
    for index, grade in enumerate(RANK_EQUIVALENTS, start=1)
    for alias in {*RANK_EQUIVALENTS[grade], grade}
}


def query_opportunities(
    records: Sequence[OpportunityRecord],
    query: OpportunityQuery,
) -> list[OpportunityRecord]:
    filtered = [record for record in records if _matches(record, query)]
    present = [record for record in filtered if _raw_sort_value(record, query.sort_by) is not None]
    missing = [record for record in filtered if _raw_sort_value(record, query.sort_by) is None]
    present.sort(
        key=lambda record: (
            _normalized_sort_value(record, query.sort_by),
            record.source_order if record.source_order is not None else 10**9,
        ),
        reverse=query.direction is SortDirection.descending,
    )
    return [*present, *missing]


def _matches(record: OpportunityRecord, query: OpportunityQuery) -> bool:
    if query.opportunity_types and record.opportunity_type not in query.opportunity_types:
        return False
    checks = [
        (query.rank, record.rank),
        (query.mos, record.mos),
        (query.location, record.location),
        (query.source, record.source_name),
    ]
    if any(needle and needle.casefold() not in (value or "").casefold() for needle, value in checks):
        return False
    if query.keyword:
        haystack = " ".join(
            value or ""
            for value in [
                record.title,
                record.unit,
                record.location,
                record.mos,
                record.rank,
                record.description,
                record.notes,
            ]
        ).casefold()
        if query.keyword.casefold() not in haystack:
            return False
    return True


def _raw_sort_value(
    record: OpportunityRecord,
    field: CareerOpportunitySortField,
) -> object | None:
    return getattr(record, field.value, None)


def _normalized_sort_value(
    record: OpportunityRecord,
    field: CareerOpportunitySortField,
) -> object:
    value = _raw_sort_value(record, field)
    if field is CareerOpportunitySortField.rank:
        normalized = str(value or "").upper().replace("-", "").replace(" ", "")
        return (GRADE_ORDER.get(normalized, 10**6), normalized)
    if field is CareerOpportunitySortField.opportunity_type:
        return record.opportunity_type.value
    if isinstance(value, str):
        return value.casefold()
    return value if value is not None else ""
