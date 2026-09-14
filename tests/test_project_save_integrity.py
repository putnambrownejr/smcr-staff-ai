from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest
from app.services.user_docs.store import UserDocsStore


def test_same_title_project_saves_preserve_each_draft(tmp_path: Path) -> None:
    store = UserDocsStore(tmp_path / "docs", tmp_path / "projects")
    category = UserDocCategory.generations
    entries = [
        store.create(category, "audit-user", UserDocCreateRequest(title="AAR", body=f"Draft {i}"))
        for i in range(3)
    ]
    # Includes simultaneous saves: exists() followed by write_text() is unsafe.
    with ThreadPoolExecutor(max_workers=3) as pool:
        paths = list(pool.map(lambda entry: store.save_to_project(category, "audit-user", entry.id, "Drill"), entries))
    assert len(set(paths)) == 3
    for entry, path in zip(entries, paths, strict=True):
        assert entry.body in (store.projects_dir / path).read_text(encoding="utf-8")
    assert store.list_category(category, "audit-user") == []


def test_existing_project_file_is_never_replaced(tmp_path: Path) -> None:
    store = UserDocsStore(tmp_path / "docs", tmp_path / "projects")
    products = store.projects_dir / "drill" / "products"
    products.mkdir(parents=True)
    existing = products / "aar.md"
    existing.write_text("Previously reviewed product", encoding="utf-8")
    entry = store.create(UserDocCategory.generations, "audit-user", UserDocCreateRequest(title="AAR", body="New draft"))
    saved = store.save_to_project(UserDocCategory.generations, "audit-user", entry.id, "Drill")
    assert existing.read_text(encoding="utf-8") == "Previously reviewed product"
    assert saved.name != existing.name
    assert "New draft" in (store.projects_dir / saved).read_text(encoding="utf-8")
