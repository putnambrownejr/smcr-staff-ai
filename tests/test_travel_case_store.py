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
                attached_receipt_categories=["lodging"],
                attachment_names=["Hilton_folio.pdf"],
                attachment_follow_up_prompts=["Still collect or upload locally: rental car."],
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
                attached_receipt_categories=["airfare or ticketed itinerary", "rental car"],
                attachment_names=["Enterprise_receipt.pdf", "flight_itinerary.pdf"],
                attachment_follow_up_prompts=[
                    "Attached receipt evidence appears to cover: airfare or ticketed itinerary, rental car."
                ],
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
    assert "Hilton_folio.pdf" in record.attachment_names
    assert "Enterprise_receipt.pdf" in record.attachment_names
    assert "airfare or ticketed itinerary" in {item.lower() for item in record.attached_receipt_categories}


def test_travel_case_store_links_local_receipt_context(tmp_path: Path) -> None:
    from app.schemas.context import LocalContextMetadata

    store = TravelCaseStore(tmp_path / "travel-cases")
    user_key = "capt-travel"
    record = store.upsert_many(
        user_key,
        [
            TravelEmailCaseSummary(
                title="CI Travel itinerary",
                source_subject="CI Travel itinerary",
                message_received_at=datetime(2026, 6, 1, 14, 30, tzinfo=UTC),
                travel_status="post_travel",
                travel_start=date(2026, 6, 6),
                travel_end=date(2026, 6, 8),
                voucher_due_date=date(2026, 6, 13),
                receipts_to_collect=["lodging", "rental car"],
            )
        ],
    )[0]
    linked = store.link_receipt(
        user_key=user_key,
        trip_id=record.trip_id,
        context=LocalContextMetadata(
            context_id="0123456789abcdef",
            filename="Hilton_folio.pdf",
            content_type="application/pdf",
            size_bytes=123,
            sha256="a" * 64,
            uploaded_at=datetime(2026, 6, 9, 10, 0, tzinfo=UTC),
            document_type="travel_receipt",
        ),
    )

    assert "0123456789abcdef" in linked.linked_receipt_context_ids
    assert "Hilton_folio.pdf" in linked.attachment_names
    assert "lodging" in {item.lower() for item in linked.attached_receipt_categories}
