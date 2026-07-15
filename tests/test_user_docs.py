from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.user_docs import get_user_docs_store
from app.core.config import get_settings
from app.main import app
from app.services.user_docs.store import UserDocsStore

VALID_USER_KEY = "a" * 24


@pytest.fixture()
def user_docs_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    store = UserDocsStore(tmp_path / "user-docs", tmp_path / "projects")
    monkeypatch.setenv("LOCAL_API_KEY", "docs-secret")
    get_settings.cache_clear()
    app.dependency_overrides[get_user_docs_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def _headers() -> dict[str, str]:
    return {"X-Local-API-Key": "docs-secret"}


def test_user_docs_require_configured_passkey(user_docs_client: TestClient) -> None:
    without_key = user_docs_client.get(f"/user-docs/notebook/{VALID_USER_KEY}")
    wrong_key = user_docs_client.get(
        f"/user-docs/notebook/{VALID_USER_KEY}",
        headers={"X-Local-API-Key": "wrong"},
    )

    assert without_key.status_code == 401
    assert wrong_key.status_code == 401


def test_notebook_crud_round_trips(user_docs_client: TestClient) -> None:
    created = user_docs_client.post(
        f"/user-docs/notebook/{VALID_USER_KEY}",
        headers=_headers(),
        json={"title": "Drill locker combo", "body": "Locker 114, combo 12-28-6."},
    )
    assert created.status_code == 201
    doc = created.json()
    assert doc["title"] == "Drill locker combo"
    assert doc["body"] == "Locker 114, combo 12-28-6."
    assert doc["category"] == "notebook"

    listed = user_docs_client.get(f"/user-docs/notebook/{VALID_USER_KEY}", headers=_headers())
    assert listed.status_code == 200
    assert [d["id"] for d in listed.json()] == [doc["id"]]

    updated = user_docs_client.patch(
        f"/user-docs/notebook/{VALID_USER_KEY}/{doc['id']}",
        headers=_headers(),
        json={"body": "Locker 114, combo 12-28-6. Backup key with S-4."},
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "Locker 114, combo 12-28-6. Backup key with S-4."
    assert updated.json()["title"] == "Drill locker combo"

    deleted = user_docs_client.delete(f"/user-docs/notebook/{VALID_USER_KEY}/{doc['id']}", headers=_headers())
    assert deleted.status_code == 204

    empty = user_docs_client.get(f"/user-docs/notebook/{VALID_USER_KEY}", headers=_headers())
    assert empty.json() == []


def test_fitrep_structured_fields_round_trip(user_docs_client: TestClient) -> None:
    created = user_docs_client.post(
        f"/user-docs/fitreps/{VALID_USER_KEY}",
        headers=_headers(),
        json={
            "title": "Diaz, M. -- AUG25-JUL26",
            "fields": {
                "name": "Diaz, M.",
                "rank": "Cpl",
                "scores": {"mission": 5, "individual": 6, "leadership": 5, "intellect": 4, "fitness": 6},
                "statement": "Consistently reliable NCO.",
            },
        },
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]

    fetched = user_docs_client.get(f"/user-docs/fitreps/{VALID_USER_KEY}/{doc_id}", headers=_headers())
    assert fetched.status_code == 200
    fields = fetched.json()["fields"]
    assert fields["scores"]["leadership"] == 5
    assert fields["statement"] == "Consistently reliable NCO."


def test_unknown_doc_returns_404(user_docs_client: TestClient) -> None:
    response = user_docs_client.get(f"/user-docs/notebook/{VALID_USER_KEY}/does-not-exist", headers=_headers())
    assert response.status_code == 404

    patch_response = user_docs_client.patch(
        f"/user-docs/notebook/{VALID_USER_KEY}/does-not-exist",
        headers=_headers(),
        json={"title": "x"},
    )
    assert patch_response.status_code == 404

    delete_response = user_docs_client.delete(
        f"/user-docs/notebook/{VALID_USER_KEY}/does-not-exist", headers=_headers()
    )
    assert delete_response.status_code == 404


def test_initial_counseling_preserves_optional_fitrep_link(user_docs_client: TestClient) -> None:
    created = user_docs_client.post(
        f"/user-docs/generations/{VALID_USER_KEY}",
        headers=_headers(),
        json={
            "title": "Initial Counseling",
            "fields": {
                "templateType": "counseling",
                "kind": "Staff product",
                "data": {
                    "linkedFitrepId": "abc123def456",
                    "marineName": "Diaz, M.",
                    "rank": "Cpl",
                    "unit": "Supply Co",
                    "duties": "Maintain accountable records.",
                },
            },
        },
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]

    fetched = user_docs_client.get(
        f"/user-docs/generations/{VALID_USER_KEY}/{doc_id}", headers=_headers()
    )
    assert fetched.status_code == 200
    fields = fetched.json()["fields"]
    assert fields["templateType"] == "counseling"
    assert fields["data"]["linkedFitrepId"] == "abc123def456"
    assert fields["data"]["marineName"] == "Diaz, M."


def test_save_to_project_creates_project_and_removes_the_draft(
    user_docs_client: TestClient, tmp_path: Path
) -> None:
    created = user_docs_client.post(
        f"/user-docs/generations/{VALID_USER_KEY}",
        headers=_headers(),
        json={"title": "AT SITREP draft", "body": "# SITREP\n\nBody text."},
    )
    doc_id = created.json()["id"]

    saved = user_docs_client.post(
        f"/user-docs/generations/{VALID_USER_KEY}/{doc_id}/save-to-project",
        headers=_headers(),
        json={"project": "AT 2026"},
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["path"] == "at-2026/products/at-sitrep-draft.md"

    project_file = tmp_path / "projects" / "at-2026" / "products" / "at-sitrep-draft.md"
    assert project_file.exists()
    assert "Body text." in project_file.read_text(encoding="utf-8")
    readme = tmp_path / "projects" / "at-2026" / "README.md"
    assert readme.exists()

    gone = user_docs_client.get(f"/user-docs/generations/{VALID_USER_KEY}/{doc_id}", headers=_headers())
    assert gone.status_code == 404


def test_save_to_project_rejects_path_traversal(user_docs_client: TestClient) -> None:
    created = user_docs_client.post(
        f"/user-docs/notebook/{VALID_USER_KEY}",
        headers=_headers(),
        json={"title": "test", "body": "x"},
    )
    doc_id = created.json()["id"]

    response = user_docs_client.post(
        f"/user-docs/notebook/{VALID_USER_KEY}/{doc_id}/save-to-project",
        headers=_headers(),
        json={"project": "../../etc"},
    )
    # The traversal segments get slugified away entirely, leaving "etc" -- a
    # perfectly normal (if new) project name, not an escape from projects_dir.
    assert response.status_code == 200
    assert response.json()["path"].startswith("etc/")


def test_list_projects_returns_explicit_demo_metadata(user_docs_client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "projects" / "ven-fhadr-jun26").mkdir(parents=True)
    demo = tmp_path / "projects" / "repo-maintenance"
    demo.mkdir(parents=True)
    (demo / ".smcr-project.json").write_text(
        '{"name":"repo-maintenance","is_demo":true}', encoding="utf-8"
    )
    malformed = tmp_path / "projects" / "cuba-sitrep"
    malformed.mkdir(parents=True)
    (malformed / ".smcr-project.json").write_text("not-json", encoding="utf-8")

    response = user_docs_client.get("/user-docs/projects", headers=_headers())

    assert response.status_code == 200
    assert response.json() == [
        {"name": "cuba-sitrep", "is_demo": False},
        {"name": "repo-maintenance", "is_demo": True},
        {"name": "ven-fhadr-jun26", "is_demo": False},
    ]


def test_notebook_and_fitreps_are_stored_in_separate_category_folders(tmp_path: Path) -> None:
    from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest

    store = UserDocsStore(tmp_path / "user-docs", tmp_path / "projects")
    store.create(UserDocCategory.notebook, VALID_USER_KEY, UserDocCreateRequest(title="a note"))
    store.create(UserDocCategory.fitreps, VALID_USER_KEY, UserDocCreateRequest(title="a fitrep"))

    assert (tmp_path / "user-docs" / "Notebook").exists()
    assert (tmp_path / "user-docs" / "FitReps").exists()
    assert (tmp_path / "user-docs" / "Generations").exists()
