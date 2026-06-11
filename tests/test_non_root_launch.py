from importlib import import_module
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.config import get_settings


def test_app_serves_dashboard_static_and_seed_data_from_non_root_cwd(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SMCR_STAFF_AI_HOME", str(tmp_path / "state"))
    get_settings.cache_clear()

    org_module = import_module("app.api.routes.org")
    org_module.clear_org_service_cache()
    main_module = import_module("app.main")
    app = main_module.create_app()
    client = TestClient(app)

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200
    assert "text/html" in dashboard_response.headers["content-type"]
    assert "<html" in dashboard_response.text.lower()

    css_response = client.get("/static/dashboard/dashboard.css")
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert css_response.text.strip()

    org_response = client.get("/org/units")
    assert org_response.status_code == 200
    assert org_response.json()

    get_settings.cache_clear()
