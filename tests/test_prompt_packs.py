from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_prompt_packs_lists_real_repo_files_excluding_readme() -> None:
    client = TestClient(app)

    response = client.get("/prompt-packs")

    assert response.status_code == 200
    body = response.json()
    slugs = {pack["slug"] for pack in body["packs"]}
    assert "readme" not in slugs
    assert "staff-products" in slugs
    assert body["total"] == len(body["packs"])
    staff_products = next(p for p in body["packs"] if p["slug"] == "staff-products")
    assert "Staff Products" in staff_products["title"]
    assert staff_products["content"].startswith("#")
