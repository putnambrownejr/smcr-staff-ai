"""Tests for the virtual staff round table endpoint."""

from __future__ import annotations

import json
import threading
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.external_processing import DisclosureMode, ExternalProcessingPreview
from app.services.agents.roundtable import resolve_participants
from app.services.llm_client import ScenarioGenerationResult, ScenarioGenerationStatus

SCENARIO_INPUT = (
    "A magnitude 7.1 earthquake struck La Guaira, Venezuela. "
    "There are 500 casualties and 10,000 displaced people. "
    "The port is damaged and a MEU supports FHADR operations."
)


# ---------------------------------------------------------------------------
# Participant auto-selection
# ---------------------------------------------------------------------------

def test_auto_selection_includes_core_and_triggered_sections() -> None:
    participants, auto = resolve_participants(SCENARIO_INPUT, [], "chief-of-staff")
    assert "staff-s2" in participants
    assert "planning-advisor" in participants
    assert "staff-g9" in participants  # earthquake / displaced / humanitarian
    assert "staff-s4" in participants  # port
    assert "staff-surgeon" in participants  # casualties
    assert "chief-of-staff" not in participants
    assert "staff-g9" in auto


def test_explicit_agents_bypass_auto_selection() -> None:
    participants, auto = resolve_participants(SCENARIO_INPUT, ["staff-g9", "staff-s2"], "chief-of-staff")
    assert participants == ["staff-g9", "staff-s2"]
    assert auto == []


def test_synthesizer_never_sits_as_participant() -> None:
    participants, _ = resolve_participants(SCENARIO_INPUT, ["staff-g9", "chief-of-staff"], "chief-of-staff")
    assert participants == ["staff-g9"]


# ---------------------------------------------------------------------------
# Local template mode (no external LLM)
# ---------------------------------------------------------------------------

def test_roundtable_local_mode_runs_parallel_council_and_synthesis() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9", "staff-s2", "staff-s4"],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["participants"] == ["staff-g9", "staff-s2", "staff-s4"]
    assert len(data["rounds"]) == 1
    assert data["rounds"][0]["name"] == "opening_assessments"
    entry_ids = [entry["agent_id"] for entry in data["rounds"][0]["entries"]]
    assert entry_ids == ["staff-g9", "staff-s2", "staff-s4"]
    for entry in data["rounds"][0]["entries"]:
        assert entry["scenario_output"] is None
        assert entry["scenario_output_status"] == "template_only"
    assert any("Cross-review round skipped" in warning for warning in data["warnings"])
    assert data["synthesis"] is not None
    assert data["synthesis"]["agent_id"] == "chief-of-staff"
    assert data["assessments"] == {}


def test_roundtable_rounds_1_has_no_skip_warning() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9"],
            "rounds": 1,
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["rounds"]) == 1
    assert not any("Cross-review" in warning for warning in data["warnings"])


def test_roundtable_null_synthesizer_skips_synthesis() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9", "staff-s2"],
            "synthesizer": None,
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    assert response.json()["synthesis"] is None


def test_roundtable_unknown_agent_returns_404() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={"scenario": SCENARIO_INPUT, "agents": ["nonexistent-agent"]},
    )

    assert response.status_code == 404


def test_roundtable_auto_selection_via_endpoint() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "staff-g9" in data["participants"]
    assert "staff-g9" in data["auto_selected"]


def test_roundtable_training_product_request_works_without_scenario_detection() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": "Build a battalion communications training product for a drill weekend.",
            "agents": ["staff-s6", "staff-opso"],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["rounds"][0]["entries"]) == 2
    for entry in data["rounds"][0]["entries"]:
        assert entry["answer"]


def test_roundtable_preview_endpoint_local_mode() -> None:
    response = TestClient(app).post(
        "/agents/roundtable/external-processing-preview",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9"],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["required"] is False
    assert data["external_available"] is False


# ---------------------------------------------------------------------------
# External mode (mocked LLM) — cross-review and synthesis handoffs
# ---------------------------------------------------------------------------

def _generated(answer: str, scenario_output: dict[str, object]) -> ScenarioGenerationResult:
    return ScenarioGenerationResult(
        content=json.dumps({"answer": answer, "scenario_output": scenario_output}),
        status=ScenarioGenerationStatus.generated,
        preview=ExternalProcessingPreview(
            required=True,
            external_available=True,
            scope_label="roundtable:test",
        ),
        disclosure_mode=DisclosureMode.sanitized,
    )


@patch("app.services.llm_client.generate_scenario_response")
def test_roundtable_cross_review_passes_assessments_between_agents(mock_generate: MagicMock) -> None:
    recorded_templates: list[str] = []
    record_lock = threading.Lock()

    def fake_generate(
        system_prompt: str, template: str, user_input: str, **kwargs: object
    ) -> ScenarioGenerationResult:
        with record_lock:
            recorded_templates.append(template)
        if "CIVIL ESTIMATE" in template:
            return _generated(
                "G-9 civil assessment",
                {"role": "g9", "civil_situation": {"area": "La Guaira", "population": "10,000 displaced"}},
            )
        if "INTELLIGENCE ESTIMATE" in template:
            return _generated(
                "S-2 intelligence assessment",
                {"role": "s2", "bottom_line": "Port access is the main uncertainty."},
            )
        return _generated(
            "Command watch list",
            {"role": "cos", "immediate_actions": ["Confirm port access."]},
        )

    mock_generate.side_effect = fake_generate

    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9", "staff-s2"],
            "rounds": 2,
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Both rounds ran: opening + cross-review, then synthesis.
    assert [r["name"] for r in data["rounds"]] == ["opening_assessments", "cross_review"]
    assert mock_generate.call_count == 5  # 2 opening + 2 cross-review + 1 synthesis

    # Cross-review entries carry validated structured output.
    for entry in data["rounds"][1]["entries"]:
        assert entry["scenario_output_status"] == "validated"

    # Final assessments include every role, synthesis included.
    assert set(data["assessments"]) == {"g9", "s2", "cos"}
    assert data["assessments"]["g9"]["civil_situation"]["area"] == "La Guaira"
    assert data["synthesis"]["scenario_output"]["immediate_actions"] == ["Confirm port access."]

    # Opening round templates carry no prior assessments; cross-review and synthesis do.
    opening_templates = recorded_templates[:2]
    later_templates = recorded_templates[2:]
    assert all("PRIOR STAFF ASSESSMENTS" not in template for template in opening_templates)
    assert all("PRIOR STAFF ASSESSMENTS" in template for template in later_templates)

    # Cross-review sees the *other* agent's assessment, not its own stale copy.
    cross_g9_template = next(t for t in later_templates if "CIVIL ESTIMATE" in t)
    assert "Port access is the main uncertainty." in cross_g9_template


@pytest.fixture
def external_llm_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    from app.services import llm_client

    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    get_settings.cache_clear()
    llm_client._llm_settings.cache_clear()
    yield
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()
    llm_client._llm_settings.cache_clear()


def test_roundtable_requires_approval_when_external_configured(external_llm_env: None) -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": SCENARIO_INPUT,
            "agents": ["staff-g9", "staff-s2"],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "preview" in detail
    assert detail["preview"]["required"] is True
