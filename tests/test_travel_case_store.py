from datetime import UTC, date, datetime
from pathlib import Path

from app.schemas.connector_digest import TravelEmailCaseSummary
from app.services.connectors.travel_case_store import TravelCaseStore


def test_travel_case_store_merges_same_trip_across_messages(tmp_path: Path) -> None:
    store = TravelCaseStore(tmp_path / "travel-cases")
    user_key = "capt-travel"

    store.upsert_many(
        user_key,
        [
            TravelEmailCaseSummary(
                title="CI Travel itinerary",
                source_subject="CI Travel itinerary",
                sender="noreply@citravel.example",
                message_received_at=datetime(2026, 6, 1, 14, 30, tzinfo=UTC),
                travel_status="upcoming_travel",
                travel_start=date(2026, 6, 6),
                travel_end=date(2026, 6, 8),
                voucher_due_date=date(2026, 6, 13),
                rental_car_expected=True,
                receipts_to_collect=["lodging", "rental car"],
            )
        ],
    )
    store.upsert_many(
        user_key,
        [
            TravelEmailCaseSummary(
                title="DTS voucher reminder",
                source_subject="DTS voucher reminder",
                sender="noreply@dts.example",
                message_received_at=datetime(2026, 6, 9, 8, 0, tzinfo=UTC),
                travel_status="post_travel",
                travel_start=date(2026, 6, 6),
                travel_end=date(2026, 6, 8),
                voucher_due_date=date(2026, 6, 13),
                receipts_to_collect=["lodging", "airfare or ticketed itinerary"],
            )
        ],
    )

    records = store.list_cases(user_key)
    assert len(records) == 1
    record = records[0]
    assert record.travel_status == "post_travel"
    assert record.voucher_due_date == date(2026, 6, 13)
    assert "CI Travel itinerary" in record.source_subjects
    assert "DTS voucher reminder" in record.source_subjects
    assert "rental car" in {item.lower() for item in record.receipts_to_collect}
