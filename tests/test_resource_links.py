from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.resource_links import get_resource_links_store
from app.core.config import get_settings
from app.main import app
from app.services.staff.resource_links_store import ResourceLinksStore

SEED_PATH = Path("data/seed/resource_links.json")


@pytest.fixture()
def resource_links_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    seed_path = tmp_path / "resource-links.json"
    seed_path.write_text(
        json.dumps(
            [
                {
                    "id": "seed-mol",
                    "title": "Marine Online",
                    "url": "https://www.mol.usmc.mil/",
                    "category": "admin_pay",
                    "description": "Personnel and administrative services.",
                    "tags": ["admin"],
                }
            ]
        ),
        encoding="utf-8",
    )
    store = ResourceLinksStore(tmp_path / "resource-links", seed_path)
    monkeypatch.setenv("LOCAL_API_KEY", "links-secret")
    get_settings.cache_clear()
    app.dependency_overrides[get_resource_links_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_resource_links_require_configured_passkey(resource_links_client: TestClient) -> None:
    without_key = resource_links_client.get("/resource-links/capt-links")
    wrong_key = resource_links_client.get(
        "/resource-links/capt-links",
        headers={"X-Local-API-Key": "wrong"},
    )

    assert without_key.status_code == 401
    assert wrong_key.status_code == 401


def test_resource_links_authenticated_crud(resource_links_client: TestClient) -> None:
    headers = {"X-Local-API-Key": "links-secret"}

    initial = resource_links_client.get("/resource-links/capt-links", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["links"][0]["title"] == "Marine Online"
    assert initial.json()["categories"]["unit"] == "Unit-specific"

    created = resource_links_client.post(
        "/resource-links/capt-links",
        headers=headers,
        json={
            "title": "Unit SharePoint",
            "url": "https://unit.example.mil/sites/staff",
            "category": "unit",
            "description": "Working files for the unit staff.",
            "tags": [],
        },
    )
    assert created.status_code == 201
    created_link = created.json()
    assert created_link["is_seed"] is False

    listed = resource_links_client.get("/resource-links/capt-links", headers=headers)
    assert {item["title"] for item in listed.json()["links"]} == {"Marine Online", "Unit SharePoint"}

    deleted = resource_links_client.delete(
        f"/resource-links/capt-links/{created_link['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204

    final = resource_links_client.get("/resource-links/capt-links", headers=headers)
    assert [item["title"] for item in final.json()["links"]] == ["Marine Online"]


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(document.domain)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "https://",
        "https://example.mil/has a space",
    ],
)
def test_resource_links_reject_non_http_or_malformed_urls(
    resource_links_client: TestClient,
    url: str,
) -> None:
    response = resource_links_client.post(
        "/resource-links/capt-links",
        headers={"X-Local-API-Key": "links-secret"},
        json={"title": "Unsafe link", "url": url, "category": "unit", "tags": []},
    )

    assert response.status_code == 422


def test_seed_resource_links_do_not_repeat_destinations() -> None:
    links = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    normalized_urls = [item["url"].rstrip("/").lower() for item in links]

    assert len(normalized_urls) == len(set(normalized_urls))
