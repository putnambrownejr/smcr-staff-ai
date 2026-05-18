from datetime import UTC, date, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.travel_cases import get_context_store, get_travel_case_store
from app.main import app
from app.schemas.connector_digest import TravelEmailCaseSummary
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.storage.local_context_store import LocalContextStore


def test_travel_case_route_links_local_receipt_context(tmp_path: Path) -> None:
    travel_case_store = TravelCaseStore(tmp_path / "travel-cases")
    context_store = LocalContextStore(tmp_path / "context")
    case = travel_case_store.upsert_many(
        "capt-travel",
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
    receipt = context_store.save(
        filename="Enterprise_receipt.pdf",
        content=b"%PDF-1.4 fake receipt bytes",
        content_type="application/pdf",
        document_type="travel_receipt",
        tags=["travel", "receipt"],
    )

    app.dependency_overrides[get_travel_case_store] = lambda: travel_case_store
    app.dependency_overrides[get_context_store] = lambda: context_store
    client = TestClient(app)
    try:
        response = client.post(
            f"/travel-cases/capt-travel/{case.trip_id}/link-receipt",
            json={
                "user_key": "capt-travel",
                "context_id": receipt.context_id,
                "receipt_category": "rental car",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert receipt.context_id in payload["linked_receipt_context_ids"]
        assert "Enterprise_receipt.pdf" in payload["attachment_names"]
        assert "rental car" in {item.lower() for item in payload["attached_receipt_categories"]}
        assert payload["attachment_follow_up_prompts"]
    finally:
        app.dependency_overrides.clear()

