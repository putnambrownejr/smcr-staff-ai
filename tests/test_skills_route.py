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


def test_skills_route_tags_audience_and_lists_only_real_skills() -> None:
    import os

    client = TestClient(app)
    payload = client.get("/skills").json()
    by_name = {item["name"]: item for item in payload["skills"]}

    # Staff-work skills vs repo-development skills are distinguished by audience.
    assert by_name["chief-brief-ops"]["audience"] == "staff"
    assert by_name["frontend-design"]["audience"] == "development"

    # The catalog must not list skills that have no folder in skills/.
    skill_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
    folders = {d for d in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, d))}
    assert set(by_name) <= folders
    for phantom in ("systematic-debugging", "brainstorming", "grill-me"):
        assert phantom not in by_name
