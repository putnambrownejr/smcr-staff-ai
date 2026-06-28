"""Tests for LLM-powered scenario template population."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_client import generate_scenario_response


# ---------------------------------------------------------------------------
# LLM client unit tests
# ---------------------------------------------------------------------------


class TestGenerateScenarioResponse:
    """Tests for the generate_scenario_response function."""

    @patch("app.services.llm_client._llm_settings")
    def test_returns_none_without_api_key(self, mock_settings):
        mock_settings.return_value = (None, "https://api.openai.com/v1", "gpt-4o-mini")
        result = generate_scenario_response("system", "template", "user input")
        assert result is None

    @patch("app.services.llm_client._llm_settings")
    def test_returns_none_with_empty_api_key(self, mock_settings):
        mock_settings.return_value = ("", "https://api.openai.com/v1", "gpt-4o-mini")
        result = generate_scenario_response("system", "template", "user input")
        assert result is None

    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_returns_llm_content_on_success(self, mock_settings, mock_client_cls):
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Populated assessment content"}}],
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = generate_scenario_response("system prompt", "template text", "scenario input")
        assert result == "Populated assessment content"

        call_args = mock_client.post.call_args
        json_body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert json_body["model"] == "gpt-4o-mini"
        assert len(json_body["messages"]) == 2
        assert "template text" in json_body["messages"][0]["content"]

    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_returns_none_on_http_error(self, mock_settings, mock_client_cls):
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.side_effect = Exception("Connection failed")
        mock_client_cls.return_value = mock_client

        result = generate_scenario_response("system", "template", "input")
        assert result is None

    @patch("app.services.llm_client.httpx.Client")
    @patch("app.services.llm_client._llm_settings")
    def test_returns_none_on_empty_content(self, mock_settings, mock_client_cls):
        mock_settings.return_value = ("sk-test", "https://api.openai.com/v1", "gpt-4o-mini")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": ""}}],
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = generate_scenario_response("system", "template", "input")
        assert result is None


# ---------------------------------------------------------------------------
# _try_llm_populate tests
# ---------------------------------------------------------------------------


class TestTryLlmPopulate:
    """Tests for the _try_llm_populate helper."""

    @patch("app.services.llm_client.generate_scenario_response")
    def test_returns_llm_result_when_available(self, mock_gen):
        from app.services.agents.staff_advisor_agent import _try_llm_populate

        mock_gen.return_value = "LLM populated text"
        result = _try_llm_populate("template text", "scenario input", "system prompt")
        assert result == "LLM populated text"
        mock_gen.assert_called_once_with("system prompt", "template text", "scenario input")

    @patch("app.services.llm_client.generate_scenario_response")
    def test_falls_back_to_template_with_notice_when_llm_returns_none(self, mock_gen):
        from app.services.agents.staff_advisor_agent import _try_llm_populate

        mock_gen.return_value = None
        result = _try_llm_populate("original template", "scenario input", "system prompt")
        assert result.startswith("original template")
        assert "LLM_API_KEY" in result


# ---------------------------------------------------------------------------
# Agent integration tests — verify LLM is called in scenario mode
# ---------------------------------------------------------------------------


SCENARIO_INPUT = (
    "A 7.1 magnitude earthquake has struck La Guaira, Venezuela. "
    "Estimated 500 casualties, 10,000 displaced. The port is damaged. "
    "A MEU is tasked to support FHADR operations."
)


class TestStaffAdvisorScenarioLLM:
    """StaffAdvisorAgent scenario mode calls LLM."""

    @patch("app.services.llm_client.generate_scenario_response")
    def test_g9_scenario_calls_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_gen.return_value = "LLM-populated G-9 civil estimate"
        agents = {a.metadata.id: a for a in build_staff_advisor_agents()}
        g9 = agents["staff-g9"]
        ctx = AgentContext(extra={})
        resp = g9.run(SCENARIO_INPUT, ctx)
        assert mock_gen.called
        assert "LLM-populated G-9 civil estimate" in resp.answer

    @patch("app.services.llm_client.generate_scenario_response")
    def test_g9_scenario_falls_back_without_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        mock_gen.return_value = None
        agents = {a.metadata.id: a for a in build_staff_advisor_agents()}
        g9 = agents["staff-g9"]
        ctx = AgentContext(extra={})
        resp = g9.run(SCENARIO_INPUT, ctx)
        assert "CIVIL ESTIMATE" in resp.answer
        assert "[Extract from scenario" in resp.answer
        assert "LLM_API_KEY" in resp.answer

    @patch("app.services.llm_client.generate_scenario_response")
    def test_framework_mode_skips_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.staff_advisor_agent import build_staff_advisor_agents

        agents = {a.metadata.id: a for a in build_staff_advisor_agents()}
        g9 = agents["staff-g9"]
        ctx = AgentContext(extra={})
        resp = g9.run("What is the role of a G-9 advisor?", ctx)
        mock_gen.assert_not_called()
        assert "SCENARIO ASSESSMENT" not in resp.answer


class TestPlanningAdvisorScenarioLLM:
    """PlanningAdvisorAgent scenario mode calls LLM."""

    @patch("app.services.llm_client.generate_scenario_response")
    def test_scenario_calls_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.planning_advisor_agent import build_planning_advisor_agent

        mock_gen.return_value = "LLM-populated mission analysis"
        agent = build_planning_advisor_agent()
        ctx = AgentContext(extra={})
        resp = agent.run(SCENARIO_INPUT, ctx)
        assert mock_gen.called
        assert "LLM-populated mission analysis" in resp.answer

    @patch("app.services.llm_client.generate_scenario_response")
    def test_scenario_falls_back_without_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.planning_advisor_agent import build_planning_advisor_agent

        mock_gen.return_value = None
        agent = build_planning_advisor_agent()
        ctx = AgentContext(extra={})
        resp = agent.run(SCENARIO_INPUT, ctx)
        assert "MISSION ANALYSIS" in resp.answer
        assert "LLM_API_KEY" in resp.answer


class TestChiefOfStaffScenarioLLM:
    """ChiefOfStaffAideAgent scenario mode calls LLM."""

    @patch("app.services.llm_client.generate_scenario_response")
    def test_scenario_calls_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent

        mock_gen.return_value = "LLM-populated watch list"
        agent = build_chief_of_staff_agent()
        ctx = AgentContext(extra={})
        resp = agent.run(SCENARIO_INPUT, ctx)
        assert mock_gen.called
        assert "LLM-populated watch list" in resp.answer

    @patch("app.services.llm_client.generate_scenario_response")
    def test_scenario_falls_back_without_llm(self, mock_gen):
        from app.services.agents.base import AgentContext
        from app.services.agents.chief_of_staff_agent import build_chief_of_staff_agent

        mock_gen.return_value = None
        agent = build_chief_of_staff_agent()
        ctx = AgentContext(extra={})
        resp = agent.run(SCENARIO_INPUT, ctx)
        assert "COMMANDER'S WATCH LIST" in resp.answer
        assert "LLM_API_KEY" in resp.answer
