from fastapi.testclient import TestClient

from app.main import app


def test_skills_route_returns_catalog_from_readme() -> None:
    client = TestClient(app)

    response = client.get("/skills")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == len(payload["skills"])
    assert payload["total"] >= 1
    names = {item["name"] for item in payload["skills"]}
    assert "chief-brief-ops" in names
    assert "source-trust-review" in names
    assert all(item["description"] for item in payload["skills"])
