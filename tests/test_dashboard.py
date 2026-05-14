from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_route_serves_html_shell() -> None:
    client = TestClient(app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SMCR Staff AI" in response.text
    assert "/static/dashboard/dashboard.js" in response.text


def test_dashboard_assets_are_served() -> None:
    client = TestClient(app)

    response = client.get("/static/dashboard/dashboard.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
