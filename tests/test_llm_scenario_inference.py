"""Tests for approved LLM scenario inference and structured envelopes."""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.agents import ScenarioOutputStatus
from app.schemas.external_processing import (
    DisclosureMode,
    ExternalProcessingApproval,
    ExternalProcessingPreview,
)
from app.schemas.scenario_handoff import G9ScenarioOutput
from app.services.agents.base import AgentContext
from app.services.external_processing.preflight import (
    ExternalProcessingApprovalRequiredError,
    ExternalProcessingPreflightService,
)
from app.services.llm_client import (
    ScenarioGenerationResult,
    ScenarioGenerationStatus,
    generate_scenario_response,
)

SCENARIO_INPUT = (
    "A 7.1 magnitude earthquake has struck La Guaira, Venezuela. "
    "Estimated 500 casualties, 10,000 displaced. The port is damaged. "
    "A MEU is tasked to support FHADR operations."
)


def _approval_for(
    system_prompt: str,
    template: str,
    user_input: str,
    *,
    mode: DisclosureMode = DisclosureMode.sanitized,
) -> ExternalProcessingApproval:
    preview = ExternalProcessingPreflightService().build_preview(
        system_prompt=system_prompt,
        template=template,
        user_input=user_input,
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        scope_label="agent:test",
        external_available=True,
    )
    return ExternalProcessingApproval(
        disclosure_mode=mode,
        approval_digest=preview.approval_digest,
        acknowledged_finding_categories=preview.finding_categories,
        acknowledged=True,
    )


def _generated(content: str) -> ScenarioGenerationResult:
    return ScenarioGenerationResult(
        content=content,
        status=ScenarioGenerationStatus.generated,
        preview=ExternalProcessingPreview(
            required=True,
            external_available=True,
            scope_label="agent:test",
        ),
        disclosure_mode=DisclosureMode.sanitized,
    )


class TestGenerateScenarioResponse:
    @patch("app.services.llm_client._llm_settings")
    def test_returns_unavailable_without_api_key(self, mock_settings: MagicMock) -> None:
        mock_settings.return_value = (None, "https://api.openai.com/v1", "gpt-4o-mini")

        result = generate_scenario_response("system", "template", "user input")

        assert result.content is None
        assert result.status is ScenarioGenerationStatus.unavailable

    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_missing_approval_never_reaches_http(
        self,
        mock_settings: MagicMock,
        mock_client_cls: MagicMock,
    ) -> None:
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")

        with pytest.raises(ExternalProcessingApprovalRequiredError):
            generate_scenario_response("system", "template", "scenario input")

        mock_client_cls.assert_not_called()

    @patch("app.services.llm_client._record_audit")
    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_approved_payload_reaches_http(
        self,
        mock_settings: MagicMock,
        mock_client_cls: MagicMock,
        mock_audit: MagicMock,
    ) -> None:
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")
        response = MagicMock()
        response.json.return_value = {"choices": [{"message": {"content": "Populated assessment"}}]}
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.return_value = response
        mock_client_cls.return_value = client
        approval = _approval_for("system", "template", "scenario input")

        result = generate_scenario_response(
            "system",
            "template",
            "scenario input",
            approval=approval,
            scope_label="agent:test",
        )

        assert result.content == "Populated assessment"
        assert result.status is ScenarioGenerationStatus.generated
        assert result.warning_override_authorized is True
        body = client.post.call_args.kwargs["json"]
        assert body["model"] == "gpt-4o-mini"
        assert len(body["messages"]) == 2
        mock_audit.assert_called_once()

    @patch("app.services.llm_client._record_audit")
    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_http_failure_returns_failed_status(
        self,
        mock_settings: MagicMock,
        mock_client_cls: MagicMock,
        mock_audit: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = False
        client.post.side_effect = OSError("Connection failed")
        mock_client_cls.return_value = client
        approval = _approval_for("system", "template", "input")

        with caplog.at_level(logging.WARNING, logger="app.services.llm_client"):
            result = generate_scenario_response(
                "system",
                "template",
                "input",
                approval=approval,
                scope_label="agent:test",
            )

        assert result.content is None
        assert result.status is ScenarioGenerationStatus.failed
        assert result.warning_override_authorized is True
        assert "Approved LLM scenario call failed" in caplog.text
        assert "synthetic prompt marker" not in caplog.text
        mock_audit.assert_called_once()

    def test_local_only_result_does_not_authorize_warning_override(self) -> None:
        result = ScenarioGenerationResult(
            content=None,
            status=ScenarioGenerationStatus.local_only,
            preview=ExternalProcessingPreview(
                required=True,
                external_available=True,
                scope_label="agent:test",
            ),
            disclosure_mode=DisclosureMode.local_only,
        )

        assert result.warning_override_authorized is False


class TestTryLlmPopulate:
    @patch("app.services.llm_client.generate_scenario_response")
    def test_parses_answer_and_structured_output(self, mock_generate: MagicMock) -> None:
        from app.services.agents.staff_advisor_agent import _try_llm_populate

        mock_generate.return_value = _generated(
            json.dumps(
                {
                    "answer": "G-9 assessment",
                    "scenario_output": {
                        "role": "g9",
                        "civil_situation": {"area": "La Guaira"},
                    },
                }
            )
        )

        result = _try_llm_populate(
            "template",
            SCENARIO_INPUT,
            "system",
            G9ScenarioOutput,
            "g9",
        )

        assert result.answer == "G-9 assessment"
        assert result.status is ScenarioOutputStatus.validated
        assert result.scenario_output is not None
        civil_situation = result.scenario_output["civil_situation"]
        assert isinstance(civil_situation, dict)
        assert civil_situation["area"] == "La Guaira"

    @patch("app.services.llm_client.generate_scenario_response")
    def test_invalid_envelope_preserves_readable_answer(self, mock_generate: MagicMock) -> None:
        from app.services.agents.staff_advisor_agent import _try_llm_populate

        mock_generate.return_value = _generated(
            json.dumps(
                {
                    "answer": "Readable but unstructured",
                    "scenario_output": {"role": "wrong-role"},
                }
            )
        )

        result = _try_llm_populate(
            "template",
            SCENARIO_INPUT,
            "system",
            G9ScenarioOutput,
            "g9",
        )

        assert result.answer == "Readable but unstructured"
        assert result.status is ScenarioOutputStatus.invalid
        assert result.scenario_output is None


class TestScenarioAgents:
    @patch("app.services.llm_client.generate_scenario_response")
    def test_g9_scenario_uses_validated_envelope(self, mock_generate: MagicMock) -> None:
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_generate.return_value = _generated(
            json.dumps(
                {
                    "answer": "LLM-populated G-9 civil estimate",
                    "scenario_output": {
                        "role": "g9",
                        "civil_situation": {"area": "La Guaira"},
                    },
                }
            )
        )
        agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}

        response = agents["staff-g9"].run(SCENARIO_INPUT, AgentContext())

        assert response.answer == "LLM-populated G-9 civil estimate"
        assert response.scenario_output_status is ScenarioOutputStatus.validated
        assert response.scenario_output is not None

    @patch("app.services.llm_client.generate_scenario_response")
    def test_raw_local_acknowledgement_does_not_override_sensitive_warning(
        self,
        mock_generate: MagicMock,
    ) -> None:
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_generate.return_value = ScenarioGenerationResult(
            content=None,
            status=ScenarioGenerationStatus.local_only,
            preview=ExternalProcessingPreview(
                required=True,
                external_available=True,
                scope_label="agent:test",
            ),
            disclosure_mode=DisclosureMode.local_only,
        )
        context = AgentContext(
            external_processing_approval=ExternalProcessingApproval(
                disclosure_mode=DisclosureMode.local_only,
                acknowledged=True,
            )
        )
        agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}

        response = agents["staff-g9"].run(f"{SCENARIO_INPUT} COMSEC training reference.", context)

        assert response.answer.startswith("I cannot process classified")

    @patch("app.services.llm_client.generate_scenario_response")
    def test_validated_external_approval_overrides_sensitive_warning(
        self,
        mock_generate: MagicMock,
    ) -> None:
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_generate.return_value = ScenarioGenerationResult(
            content=json.dumps(
                {
                    "answer": "Acknowledged training assessment",
                    "scenario_output": {
                        "role": "g9",
                        "civil_situation": {"area": "La Guaira"},
                    },
                }
            ),
            status=ScenarioGenerationStatus.generated,
            preview=ExternalProcessingPreview(
                required=True,
                external_available=True,
                scope_label="agent:test",
            ),
            disclosure_mode=DisclosureMode.original,
            warning_override_authorized=True,
        )
        agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}

        response = agents["staff-g9"].run(f"{SCENARIO_INPUT} COMSEC training reference.", AgentContext())

        assert response.answer == "Acknowledged training assessment"

    @patch("app.services.llm_client.generate_scenario_response")
    def test_no_llm_returns_template_without_fake_handoff(self, mock_generate: MagicMock) -> None:
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_generate.return_value = ScenarioGenerationResult(
            content=None,
            status=ScenarioGenerationStatus.unavailable,
            preview=ExternalProcessingPreview(
                required=False,
                external_available=False,
                scope_label="agent:test",
            ),
        )
        agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}

        response = agents["staff-g9"].run(SCENARIO_INPUT, AgentContext())

        assert "CIVIL ESTIMATE" in response.answer
        assert response.scenario_output is None
        assert response.scenario_output_status is ScenarioOutputStatus.template_only

    @patch("app.services.llm_client.generate_scenario_response")
    def test_framework_mode_skips_llm(self, mock_generate: MagicMock) -> None:
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        agents = {agent.metadata.id: agent for agent in build_staff_advisor_agents()}

        response = agents["staff-g9"].run("What is the role of a G-9 advisor?", AgentContext())

        mock_generate.assert_not_called()
        assert response.scenario_output_status is ScenarioOutputStatus.not_applicable
