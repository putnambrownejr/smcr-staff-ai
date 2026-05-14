from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.context import get_context_store
from app.main import app
from app.services.storage.local_context_store import LocalContextStore


def test_local_context_store_does_not_affect_structure(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="drill notes.txt",
        content=b"Training-only context for local drill prep.",
        content_type="text/plain",
        tags=["drill", "local"],
    )

    assert item.affects_canonical_structure is False
    assert item.advisory_only is True
    assert store.read_preview(item.context_id) == "Training-only context for local drill prep."
    assert (tmp_path / "metadata" / f"{item.context_id}.json").exists()


def test_local_context_rejects_glob_context_id_for_delete(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="notes.txt",
        content=b"Training-only context.",
        content_type="text/plain",
    )

    assert store.delete("*") is False
    assert store.get(item.context_id) is not None


def test_local_context_upload_api(tmp_path: Path) -> None:
    def override_store() -> LocalContextStore:
        return LocalContextStore(tmp_path)

    app.dependency_overrides[get_context_store] = override_store
    client = TestClient(app)
    try:
        response = client.post(
            "/context/upload",
            files={"file": ("notes.txt", b"Local advisory context.", "text/plain")},
            data={"tags": "drill, local"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["item"]["affects_canonical_structure"] is False
        assert payload["item"]["tags"] == ["drill", "local"]

        context_id = payload["item"]["context_id"]
        read_response = client.get(f"/context/{context_id}")
        assert read_response.status_code == 200
        assert read_response.json()["text_preview"] == "Local advisory context."
    finally:
        app.dependency_overrides.clear()


def test_rqs_bio_upload_metadata_and_redacted_preview(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="bio.txt",
        content=b"BIO draft. SSN 123-45-6789. phone: 555-123-4567.",
        content_type="text/plain",
        document_type="bio",
        consent_ack=True,
    )

    assert item.document_type == "bio"
    assert item.contains_pii is True
    preview = store.read_preview(item.context_id)
    assert preview is not None
    assert "123-45-6789" not in preview
    assert "555-123-4567" not in preview
    assert "[REDACTED-SSN]" in preview
