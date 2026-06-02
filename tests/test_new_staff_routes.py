from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

API_KEY = "test-local-api-key"
HEADERS = {"X-Local-API-Key": API_KEY}


@pytest.fixture(autouse=True)
def require_local_api_key(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("LOCAL_API_KEY", API_KEY)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_xo_sync_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/xo-sync",
        headers=HEADERS,
        json={
            "title": "Battalion sync",
            "supported_event": "drill weekend",
            "command_focus": "Resolve friction points and assign owners.",
        },
    )

    assert response.status_code == 200
    assert response.json()["synchronization_matrix"]


def test_command_cell_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/command-cell",
        headers=HEADERS,
        json={
            "title": "Command cell prep",
            "supported_event": "drill weekend",
            "command_focus": "Keep the command picture current.",
        },
    )

    assert response.status_code == 200
    assert response.json()["chief_focus_board"]


def test_s1_readiness_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/s1-readiness",
        headers=HEADERS,
        json={
            "title": "S-1 prep",
            "supported_event": "drill weekend",
        },
    )

    assert response.status_code == 200
    assert response.json()["readiness_estimate"]


def test_safety_plan_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/safety-plan",
        headers=HEADERS,
        json={
            "title": "Safety prep",
            "supported_event": "field exercise",
        },
    )

    assert response.status_code == 200
    assert response.json()["orm_framework"]


def test_sel_execution_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/sel-execution",
        headers=HEADERS,
        json={
            "title": "SEL prep",
            "supported_event": "drill weekend",
        },
    )

    assert response.status_code == 200
    assert response.json()["troop_flow_plan"]


def test_lone_planner_returns_valid_response() -> None:
    response = TestClient(app).post(
        "/staff/lone-planner",
        headers=HEADERS,
        json={
            "title": "Thin staff assist",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine the next drill training plan.",
        },
    )

    assert response.status_code == 200
    assert response.json()["walk_in_brief"]
