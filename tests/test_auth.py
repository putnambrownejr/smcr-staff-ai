"""Tests for LocalApiKeyDependency behaviour — especially the empty-string edge case.

The .env.example ships with LOCAL_API_KEY="" (empty string). Auth must treat that
identically to the unset (None) case so a first-run user is never locked out.
"""
from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _clear_cache() -> None:
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_settings_cache() -> Generator[None, None, None]:
    _clear_cache()
    yield
    _clear_cache()


# ---------------------------------------------------------------------------
# No key configured — gate is open
# ---------------------------------------------------------------------------

def test_no_api_key_allows_personal_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_API_KEY", raising=False)
    _clear_cache()
    # /health is always open; /user-profile requires auth — a 404 (no profile) means auth passed
    resp = client.get("/user-profile/nobody", headers={})
    assert resp.status_code == 404  # auth passed, profile just doesn't exist


def test_empty_string_key_allows_personal_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """LOCAL_API_KEY="" must behave identically to unset — the .env.example trap."""
    monkeypatch.setenv("LOCAL_API_KEY", "")
    _clear_cache()
    resp = client.get("/user-profile/nobody", headers={})
    assert resp.status_code == 404  # auth passed, not 401


# ---------------------------------------------------------------------------
# Key configured — gate enforces correctly
# ---------------------------------------------------------------------------

def test_wrong_key_returns_401(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "secret")
    _clear_cache()
    resp = client.get("/user-profile/nobody", headers={"X-Local-API-Key": "wrong"})
    assert resp.status_code == 401


def test_correct_key_allows_access(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "secret")
    _clear_cache()
    resp = client.get("/user-profile/nobody", headers={"X-Local-API-Key": "secret"})
    assert resp.status_code == 404  # auth passed, profile just doesn't exist


def test_no_header_with_key_set_returns_401(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "secret")
    _clear_cache()
    resp = client.get("/user-profile/nobody", headers={})
    assert resp.status_code == 401
