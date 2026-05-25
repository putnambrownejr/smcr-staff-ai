from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.uniform import get_context_store
from app.main import app
from app.services.storage.local_context_store import LocalContextStore


def test_uniform_photo_review_route_stores_image_and_returns_review(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)

    def override_store() -> LocalContextStore:
        return store

    app.dependency_overrides[get_context_store] = override_store
    client = TestClient(app)
    try:
        response = client.post(
            "/uniform/photo-review",
            files={"file": ("uniform.jpg", b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg")},
            data={
                "uniform_type": "service_alpha",
                "event_context": "Drill formation",
                "visible_items": "rank insignia, ribbons/badges, grooming/hair",
                "observed_concerns": "Ribbon spacing may be off",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["uniform_type"] == "service_alpha"
        assert payload["photo_context_id"]
        assert payload["filename"] == "uniform.jpg"
        assert payload["structured_citations"]
        assert any("photo-assisted advisory review" in line.lower() for line in payload["summary_lines"])
        assert any("ribbon" in item.lower() for item in payload["what_to_verify_in_image"])
        assert store.get(payload["photo_context_id"]) is not None
    finally:
        app.dependency_overrides.clear()
