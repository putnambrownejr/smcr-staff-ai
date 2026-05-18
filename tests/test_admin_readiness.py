from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.admin import get_admin_readiness_service
from app.main import app
from app.schemas.connector_digest import TravelEmailCaseSummary
from app.schemas.session import FitrepReminder, UserSessionHandoff
from app.services.admin.readiness import AdminReadinessService
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore


def test_admin_readiness_route_surfaces_due_outs_and_document_gaps(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-admin",
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15), role="MRO")],
            admin_watch_items=["DTS voucher after drill", "Orders update before AT"],
        )
    )
    travel_case_store = TravelCaseStore(tmp_path / "travel-cases")
    travel_case_store.upsert_many(
        "capt-admin",
        [
            TravelEmailCaseSummary(
                title="CI Travel itinerary",
                source_subject="CI Travel itinerary",
                travel_status="post_travel",
                travel_start=date(2026, 6, 6),
                travel_end=date(2026, 6, 8),
                voucher_due_date=date(2026, 6, 13),
                receipts_to_collect=["lodging", "rental car"],
                attached_receipt_categories=["lodging"],
                attachment_names=["Hilton_folio.pdf"],
                attachment_follow_up_prompts=["Still collect or upload locally: rental car."],
            )
        ],
    )
    context_store.save(
        filename="orders.txt",
        content=b"Training-only orders placeholder.",
        content_type="text/plain",
        document_type="orders",
        consent_ack=True,
    )

    def override_service() -> AdminReadinessService:
        return AdminReadinessService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            travel_case_store=travel_case_store,
        )

    app.dependency_overrides[get_admin_readiness_service] = override_service
    client = TestClient(app)
    try:
        response = client.get("/admin/readiness/capt-admin")
        assert response.status_code == 200
        payload = response.json()
        assert payload["summary_lines"]
        assert payload["travel_cases"]
        assert payload["source_trust"]
        categories = {item["category"] for item in payload["items"]}
        assert {"fitrep", "admin", "documents", "travel"}.issubset(categories)
        assert any("voucher due for stored trip" in item["title"].lower() for item in payload["items"])
        assert any("attached travel receipts" in item["title"].lower() for item in payload["items"])
    finally:
        app.dependency_overrides.clear()
