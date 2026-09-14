from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest
from app.services.user_docs.store import UserDocsStore


def test_word_export_contains_structured_draft_fields(tmp_path: Path) -> None:
    store = UserDocsStore(tmp_path / "docs", tmp_path / "projects")
    draft = store.create(UserDocCategory.generations, "test", UserDocCreateRequest(
        title="Synthetic AAR", fields={"templateType": "aar", "data": {"event": "Practice", "sustains": "Keep the checklist", "improves": "Allow more time"}},
    ))
    relative = store.save_to_project(UserDocCategory.generations, "test", draft.id, "review")
    path = store.projects_dir / relative
    document = Document(BytesIO(path.with_suffix(".docx").read_bytes()))
    text = "\n".join(p.text for p in document.paragraphs)
    for content in ("Practice", "Keep the checklist", "Allow more time", "DRAFT"):
        assert content in text
        assert content in path.read_text(encoding="utf-8")
    assert store.get(UserDocCategory.generations, "test", draft.id) is None


def test_existing_word_file_is_never_replaced(tmp_path: Path) -> None:
    store = UserDocsStore(tmp_path / "docs", tmp_path / "projects")
    existing = store.projects_dir / "review" / "products" / "same.docx"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"existing product")
    draft = store.create(UserDocCategory.notebook, "test", UserDocCreateRequest(title="Same", body="new text"))
    path = store.save_to_project(UserDocCategory.notebook, "test", draft.id, "review")
    assert path.name == "same-2.md"
    assert existing.read_bytes() == b"existing product"


def test_word_render_failure_preserves_draft(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = UserDocsStore(tmp_path / "docs", tmp_path / "projects")
    draft = store.create(UserDocCategory.notebook, "test", UserDocCreateRequest(title="Same", body="keep this"))

    def fail(markdown: str) -> bytes:
        raise OSError("synthetic render failure")

    monkeypatch.setattr("app.services.user_docs.store.render_product_docx", fail)
    with pytest.raises(OSError):
        store.save_to_project(UserDocCategory.notebook, "test", draft.id, "review")
    assert store.get(UserDocCategory.notebook, "test", draft.id) is not None
    assert not list((store.projects_dir / "review" / "products").glob("*"))
