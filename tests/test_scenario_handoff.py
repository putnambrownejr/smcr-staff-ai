"""Tests for validated structured scenario handoffs."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import get_settings
from app.main import app
from app.schemas.agents import ScenarioOutputStatus
from app.schemas.external_processing import DisclosureMode, ExternalProcessingApproval, ExternalProcessingPreview
from app.schemas.scenario_handoff import (
    CoSScenarioOutput,
    G9ScenarioOutput,
    PlanningScenarioOutput,
    S2ScenarioOutput,
)
from app.services.agents.scenario_envelope import (
    ScenarioEnvelopeParser,
    ScenarioEnvelopeValidationError,
)
from app.services.llm_client import ScenarioGenerationResult, ScenarioGenerationStatus

SCENARIO_INPUT = (
    "A magnitude 7.1 earthquake struck La Guaira, Venezuela. "
    "There are 500 casualties and 10,000 displaced people. "
    "The port is damaged and a MEU supports FHADR operations."
)


def _generated(answer: str, scenario_output: dict[str, object]) -> ScenarioGenerationResult:
    return ScenarioGenerationResult(
        content=json.dumps({"answer": answer, "scenario_output": scenario_output}),
        status=ScenarioGenerationStatus.generated,
        preview=ExternalProcessingPreview(
            required=True,
            external_available=True,
            scope_label="chain:test",
        ),
        disclosure_mode=DisclosureMode.sanitized,
    )


def test_scenario_models_forbid_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        G9ScenarioOutput.model_validate({"role": "g9", "unexpected": "value"})


def test_envelope_parser_accepts_one_surrounding_code_fence() -> None:
    fence = chr(96) * 3
    content = (
        f"{fence}json\n"
        + json.dumps(
            {
                "answer": "Civil assessment",
                "scenario_output": {
                    "role": "g9",
                    "civil_situation": {"area": "La Guaira"},
                },
            }
        )
        + f"\n{fence}"
    )

    parsed = ScenarioEnvelopeParser().parse(
        content,
        output_model=G9ScenarioOutput,
        expected_role="g9",
    )

    civil_situation = parsed.scenario_output["civil_situation"]
    assert isinstance(civil_situation, dict)
    assert civil_situation["area"] == "La Guaira"


def test_envelope_parser_rejects_empty_structured_output() -> None:
    content = json.dumps(
        {
            "answer": "Looks populated",
            "scenario_output": {"role": "g9"},
        }
    )

    with pytest.raises(ScenarioEnvelopeValidationError, match="no assessment data"):
        ScenarioEnvelopeParser().parse(
            content,
            output_model=G9ScenarioOutput,
            expected_role="g9",
        )


@pytest.mark.parametrize(
    "agent_id",
    [
        "staff-g9",
        "staff-s2",
        "staff-s4",
        "staff-s6",
        "planning-advisor",
        "chief-of-staff",
    ],
)
def test_no_key_scenario_returns_template_without_fake_handoff(agent_id: str) -> None:
    response = TestClient(app).post(
        f"/agents/{agent_id}/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is None
    assert data["scenario_output_status"] == ScenarioOutputStatus.template_only


def test_non_scenario_returns_not_applicable() -> None:
    response = TestClient(app).post(
        "/agents/staff-g9/run",
        json={"input": "What does a G-9 do?", "context": {}},
    )

    assert response.status_code == 200
    assert response.json()["scenario_output_status"] == ScenarioOutputStatus.not_applicable


def test_local_chain_runs_templates_without_fake_prior_assessments() -> None:
    response = TestClient(app).post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [{"agent_id": "staff-g9"}, {"agent_id": "staff-s2"}],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert len(data["results"]) == 2
    assert all(result["scenario_output"] is None for result in data["results"])
    assert all(
        result["response"]["scenario_output_status"] == ScenarioOutputStatus.template_only
        for result in data["results"]
    )
    assert "PRIOR STAFF ASSESSMENTS" not in data["results"][1]["response"]["answer"]


@patch("app.services.llm_client.generate_scenario_response")
def test_validated_chain_passes_concrete_values_forward(mock_generate: MagicMock) -> None:
    mock_generate.side_effect = [
        _generated(
            "G-9 assessment",
            {
                "role": "g9",
                "civil_situation": {"area": "La Guaira", "population": "10,000 displaced"},
            },
        ),
        _generated(
            "S-2 assessment",
            {
                "role": "s2",
                "area_of_operations": "La Guaira",
                "bottom_line": "Port access is the main uncertainty.",
            },
        ),
        _generated(
            "Planning assessment",
            {
                "role": "planning",
                "tempo": "MCPP (deliberate)",
                "mission_analysis": {"restated_mission": "Support relief operations."},
            },
        ),
        _generated(
            "Command watch list",
            {
                "role": "cos",
                "immediate_actions": ["Confirm port access."],
            },
        ),
    ]
    response = TestClient(app).post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [
                {"agent_id": "staff-g9"},
                {"agent_id": "staff-s2"},
                {"agent_id": "planning-advisor"},
                {"agent_id": "chief-of-staff"},
            ],
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["results"][0]["scenario_output"]["civil_situation"]["area"] == "La Guaira"
    assert data["results"][3]["scenario_output"]["immediate_actions"] == ["Confirm port access."]
    second_template = mock_generate.call_args_list[1].args[1]
    planning_template = mock_generate.call_args_list[2].args[1]
    assert "La Guaira" in second_template
    assert "Port access is the main uncertainty." in planning_template


@patch("app.services.llm_client.generate_scenario_response")
def test_invalid_external_handoff_stops_before_next_call(
    mock_generate: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    get_settings.cache_clear()
    mock_generate.return_value = _generated("Readable answer", {"role": "g9"})
    approval = ExternalProcessingApproval(
        disclosure_mode=DisclosureMode.original,
        approval_digest="a" * 64,
        acknowledged=True,
    )
    try:
        response = TestClient(app).post(
            "/agents/chain",
            json={
                "scenario": SCENARIO_INPUT,
                "steps": [{"agent_id": "staff-g9"}, {"agent_id": "staff-s2"}],
                "context": {"request_is_training_or_fictional": True},
                "external_processing_approval": approval.model_dump(mode="json"),
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is False
    assert data["stopped_at_agent_id"] == "staff-g9"
    assert len(data["results"]) == 1
    assert mock_generate.call_count == 1


def test_chain_endpoint_rejects_unknown_agent() -> None:
    response = TestClient(app).post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [{"agent_id": "nonexistent-agent"}],
            "context": {},
        },
    )

    assert response.status_code == 404


def test_schema_examples_remain_constructible() -> None:
    assert S2ScenarioOutput(role="s2").role == "s2"
    assert PlanningScenarioOutput(role="planning", tempo="MCPP").tempo == "MCPP"
    assert CoSScenarioOutput(role="cos").role == "cos"
