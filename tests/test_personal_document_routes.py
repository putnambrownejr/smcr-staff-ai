from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.personal_documents import get_context_store
from app.main import app
from app.services.storage.local_context_store import LocalContextStore


def test_personal_document_detail_route_returns_preview_and_dates(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="orders.txt",
        content=b"Training-only orders placeholder.",
        content_type="text/plain",
        document_type="orders",
        review_date=date(2026, 6, 1),
        expiration_date=date(2026, 12, 1),
    )

    def override_store() -> LocalContextStore:
        return store

    app.dependency_overrides[get_context_store] = override_store
    client = TestClient(app)
    try:
        response = client.get(f"/personal-documents/{item.context_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["record"]["document_type"] == "orders"
        assert payload["record"]["review_date"] == "2026-06-01"
        assert payload["record"]["expiration_date"] == "2026-12-01"
        assert payload["text_preview"] == "Training-only orders placeholder."
    finally:
        app.dependency_overrides.clear()
