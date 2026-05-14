from fastapi.testclient import TestClient

from app.main import app


def test_demo_tool_catalog_returns_first_pass_surface() -> None:
    client = TestClient(app)

    response = client.get("/demo/tool-catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["archetype"] == "tool-only"
    names = [entry["name"] for entry in payload["tool_entries"]]
    assert "chief_brief_demo" in names
    assert "summarize_text_demo" in names
