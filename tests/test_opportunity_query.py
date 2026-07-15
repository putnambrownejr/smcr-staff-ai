from datetime import date

from app.schemas.career_opportunities import (
    CareerOpportunitySortField,
    OpportunityQuery,
    SortDirection,
)
from app.schemas.opportunities import OpportunityRecord
from app.services.opportunities.query import query_opportunities


def _records() -> list[OpportunityRecord]:
    return [
        OpportunityRecord(
            opportunity_id="ima-major",
            title="Planner",
            opportunity_type="ima",
            rank="Maj",
            mos="0505",
            location="Quantico, VA",
            source_name="Reserve Billets",
            source_order=2,
            published_at=date(2026, 7, 1),
            tracked=False,
        ),
        OpportunityRecord(
            opportunity_id="smcr-capt",
            title="Communications Officer",
            opportunity_type="smcr",
            rank="Capt",
            mos="0602",
            location="Austin, TX",
            source_name="Reserve Billets",
            source_order=1,
            tracked=False,
        ),
        OpportunityRecord(
            opportunity_id="ados-ltcol",
            title="ADOS G-6",
            opportunity_type="ados",
            rank="LtCol",
            mos="0602",
            location="New Orleans, LA",
            source_name="Active Billets",
            source_order=1,
            published_at=date(2026, 7, 10),
            tracked=False,
        ),
    ]


def test_rank_sort_uses_grade_order() -> None:
    result = query_opportunities(
        _records(),
        OpportunityQuery(
            sort_by=CareerOpportunitySortField.rank,
            direction=SortDirection.ascending,
        ),
    )

    assert [item.rank for item in result] == ["Capt", "Maj", "LtCol"]


def test_date_sort_keeps_missing_dates_last_in_both_directions() -> None:
    for direction in SortDirection:
        result = query_opportunities(
            _records(),
            OpportunityQuery(sort_by="published_at", direction=direction),
        )
        assert result[-1].published_at is None


def test_filters_compose_and_clear_to_source_order() -> None:
    result = query_opportunities(
        _records(),
        OpportunityQuery(opportunity_types=["ima", "ados"], mos="06", keyword="g-6"),
    )
    assert [item.opportunity_id for item in result] == ["ados-ltcol"]

    default = query_opportunities(_records(), OpportunityQuery())
    assert [item.source_order for item in default if item.source_name == "Reserve Billets"] == [1, 2]


def test_every_user_visible_sort_field_handles_missing_values() -> None:
    for field in CareerOpportunitySortField:
        for direction in SortDirection:
            result = query_opportunities(
                _records(),
                OpportunityQuery(sort_by=field, direction=direction),
            )
            assert len(result) == 3
