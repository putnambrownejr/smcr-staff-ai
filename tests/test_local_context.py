from pathlib import Path
import zipfile

from fastapi.testclient import TestClient
import pytest

from app.core.security import detect_pii_input
from app.api.routes.context import get_context_store
from app.main import app
from app.services.storage import local_context_store
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


def test_upload_coerces_invalid_document_type_to_other(tmp_path: Path) -> None:
    # #17: an invalid document_type must not reach storage; it falls back to "other".
    def override_store() -> LocalContextStore:
        return LocalContextStore(tmp_path)

    app.dependency_overrides[get_context_store] = override_store
    client = TestClient(app)
    try:
        response = client.post(
            "/context/upload",
            files={"file": ("x.txt", b"local", "text/plain")},
            data={"document_type": "definitely-not-a-valid-type"},
        )
        assert response.status_code == 200
        assert response.json()["item"]["document_type"] == "other"

        valid = client.post(
            "/context/upload",
            files={"file": ("y.txt", b"local", "text/plain")},
            data={"document_type": "orders"},
        )
        assert valid.status_code == 200
        assert valid.json()["item"]["document_type"] == "orders"
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


@pytest.mark.parametrize(
    ("raw_text", "redaction"),
    [
        ("SSN 123-45-6789", "[REDACTED-SSN]"),
        ("social security is noted", "[REDACTED-SSN]"),
        ("DOB: 01/02/1990", "[REDACTED-DOB]"),
        ("phone: 555-123-4567", "[REDACTED-PHONE]"),
        ("ZIP 12345-6789", "[REDACTED-ZIP]"),
        ("zip code: 12345", "[REDACTED-ZIP]"),
    ],
)
def test_pii_detection_patterns_are_redacted_from_preview(
    tmp_path: Path,
    raw_text: str,
    redaction: str,
) -> None:
    assert detect_pii_input(raw_text) is True
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="pii.txt",
        content=f"Admin note. {raw_text}.".encode(),
        content_type="text/plain",
        consent_ack=True,
    )

    preview = store.read_preview(item.context_id)

    assert preview is not None
    assert raw_text not in preview
    assert redaction in preview


def test_binary_local_context_returns_metadata_preview(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="demo.mp4",
        content=b"\x00\x00\x00\x18ftypmp42",
        content_type="video/mp4",
        document_type="training_media",
        tags=["video", "use_case"],
        consent_ack=True,
    )

    preview = store.read_preview(item.context_id)
    assert preview is not None
    assert "Binary local context item: demo.mp4" in preview
    assert "video/mp4" in preview
    assert "No text preview is available" in preview


def test_docx_local_context_returns_extracted_preview(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    docx_path = tmp_path / "outline.docx"
    with zipfile.ZipFile(docx_path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body>"
                "<w:p><w:r><w:t>Comm format notes</w:t></w:r></w:p>"
                "<w:p><w:r><w:t>PACE plan section</w:t></w:r></w:p>"
                "</w:body>"
                "</w:document>"
            ),
        )

    item = store.save(
        filename="outline.docx",
        content=docx_path.read_bytes(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        document_type="product_example",
        consent_ack=True,
    )

    preview = store.read_preview(item.context_id)
    assert preview is not None
    assert "Comm format notes" in preview
    assert "PACE plan section" in preview


def test_pdf_local_context_uses_pdf_text_extractor(tmp_path: Path, monkeypatch) -> None:
    store = LocalContextStore(tmp_path)

    monkeypatch.setattr(local_context_store, "extract_pdf_text", lambda path: "Reserve admin order reference")

    item = store.save(
        filename="admin-order.pdf",
        content=b"%PDF-1.4 fake",
        content_type="application/pdf",
        document_type="other",
        consent_ack=True,
    )

    preview = store.read_preview(item.context_id)
    assert preview is not None
    assert "Reserve admin order reference" in preview


def test_uniform_photo_local_context_returns_binary_preview(tmp_path: Path) -> None:
    store = LocalContextStore(tmp_path)
    item = store.save(
        filename="uniform.jpg",
        content=b"\xff\xd8\xff\xe0fakejpeg",
        content_type="image/jpeg",
        document_type="uniform_photo",
        consent_ack=True,
    )

    preview = store.read_preview(item.context_id)
    assert preview is not None
    assert "Binary local context item: uniform.jpg" in preview
    assert "image/jpeg" in preview
