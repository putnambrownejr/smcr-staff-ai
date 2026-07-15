from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.fitreps import get_context_store, get_fitrep_store
from app.main import app
from app.services.fitreps.store import FitrepStore
from app.services.storage.local_context_store import LocalContextStore


def test_fitrep_routes_manual_import_preview_confirm_and_analytics(tmp_path: Path) -> None:
    fitrep_store = FitrepStore(tmp_path / "fitreps")
    context_store = LocalContextStore(tmp_path / "context")
    source = context_store.save(
        filename="my-profile.txt",
        content=b"Reporting Senior: RS Alpha\nRelative Value: 91.2\nGrade: Capt\n",
        content_type="text/plain",
        document_type="fitrep",
    )
    app.dependency_overrides[get_fitrep_store] = lambda: fitrep_store
    app.dependency_overrides[get_context_store] = lambda: context_store
    client = TestClient(app)
    try:
        preview = client.post(
            "/fitreps/capt-fitrep/imports/preview",
            json={"user_key": "capt-fitrep", "context_id": source.context_id, "kind": "my_record"},
        )
        assert preview.status_code == 200
        assert preview.json()["requires_confirmation"] is True
        assert fitrep_store.get("capt-fitrep").reports == []

        confirmed = client.post(
            "/fitreps/capt-fitrep/imports/confirm",
            json={"user_key": "capt-fitrep", "kind": "my_record", "proposal": preview.json()},
        )
        assert confirmed.status_code == 201
        assert confirmed.json()["reports"][0]["source_type"] == "my_record_import"

        manual = client.post(
            "/fitreps/capt-fitrep/reports",
            json={"user_key": "capt-fitrep", "occasion": "AN", "relative_value": "94.0"},
        )
        assert manual.status_code == 201
        analytics = client.get("/fitreps/capt-fitrep/analytics")
        assert analytics.status_code == 200
        assert analytics.json()["sample_size"] == 2
    finally:
        app.dependency_overrides.clear()
