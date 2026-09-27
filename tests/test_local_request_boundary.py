from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_main_app_rejects_foreign_host() -> None:
    response = TestClient(app).get("/dashboard", headers={"host": "untrusted.invalid"})
    assert response.status_code == 400


def test_main_app_rejects_cross_origin_shutdown() -> None:
    with patch("app.api.routes.dashboard._schedule_shutdown") as shutdown:
        response = TestClient(app).post(
            "/dashboard/shutdown",
            headers={"origin": "http://untrusted.invalid"},
        )
    assert response.status_code == 403
    shutdown.assert_not_called()


def test_main_app_allows_same_origin_shutdown() -> None:
    with patch("app.api.routes.dashboard._schedule_shutdown") as shutdown:
        response = TestClient(app).post(
            "/dashboard/shutdown",
            headers={"origin": "http://testserver"},
        )
    assert response.status_code == 200
    shutdown.assert_called_once()


def test_main_app_rejects_cross_site_write_without_origin() -> None:
    with patch("app.api.routes.dashboard._schedule_shutdown") as shutdown:
        response = TestClient(app).post(
            "/dashboard/shutdown",
            headers={"sec-fetch-site": "cross-site"},
        )
    assert response.status_code == 403
    shutdown.assert_not_called()


def test_workspace_recovery_page_is_served_without_cache_or_framing() -> None:
    response = TestClient(app).get("/dashboard/workspace-recovery")
    assert response.status_code == 200
    assert "Recover your workspace" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "workspace-recovery.js" in response.text
