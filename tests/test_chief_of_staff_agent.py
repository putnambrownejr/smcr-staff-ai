"""Tests for ChiefOfStaffAideAgent — context-sensitive questions and confidence scaling."""
from __future__ import annotations

import pytest

from app.schemas.agents import Confidence
from app.services.agents.base import AgentContext
from app.services.agents.chief_of_staff_agent import (
    ChiefOfStaffAideAgent,
    _confidence,
    _follow_up_questions,
)


@pytest.fixture()
def agent() -> ChiefOfStaffAideAgent:
    return ChiefOfStaffAideAgent()


def _ctx(handoff: dict | None = None) -> AgentContext:
    return AgentContext(extra={"handoff": handoff} if handoff is not None else {})


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def test_confidence_no_handoff() -> None:
    assert _confidence({}) is Confidence.low


def test_confidence_missing_handoff_key() -> None:
    assert _confidence({"rank": "MAJ"}) is Confidence.low


def test_confidence_partial_handoff_two_fields() -> None:
    result = _confidence({"pme": ["EWS"], "drill_dates": ["2026-09-06"]})
    assert result is Confidence.low


def test_confidence_full_handoff_three_plus_fields() -> None:
    result = _confidence({
        "pme": ["EWS"],
        "fitreps": [{"occasion": "Annual", "due_date": "2026-10-01"}],
        "drill_dates": ["2026-09-06"],
        "admin_watch_items": ["Claims pending"],
    })
    assert result is Confidence.medium


# ---------------------------------------------------------------------------
# Follow-up questions — gap filling
# ---------------------------------------------------------------------------

def test_follow_up_empty_handoff_asks_drill_dates() -> None:
    qs = _follow_up_questions({})
    assert any("drill" in q.lower() for q in qs)


def test_follow_up_empty_handoff_asks_pme() -> None:
    qs = _follow_up_questions({})
    assert any("pme" in q.lower() for q in qs)


def test_follow_up_empty_handoff_asks_fitrep() -> None:
    qs = _follow_up_questions({})
    assert any("fitrep" in q.lower() for q in qs)


def test_follow_up_no_more_than_four() -> None:
    qs = _follow_up_questions({})
    assert len(qs) <= 4


# ---------------------------------------------------------------------------
# Follow-up questions — context-specific when data is present
# ---------------------------------------------------------------------------

def test_follow_up_drill_present_asks_prep_plan() -> None:
    qs = _follow_up_questions({"drill_dates": ["2026-09-06"]})
    assert any("drill-prep plan" in q.lower() or "2026-09-06" in q for q in qs)


def test_follow_up_pme_present_asks_on_track() -> None:
    qs = _follow_up_questions({"pme": ["EWS"]})
    assert any("ews" in q.lower() or "on track" in q.lower() for q in qs)


def test_follow_up_fitrep_present_asks_talking_points() -> None:
    fitrep = {"occasion": "Annual", "due_date": "2026-10-01"}
    qs = _follow_up_questions({"fitreps": [fitrep]})
    assert any("talking points" in q.lower() or "annual" in q.lower() for q in qs)


def test_follow_up_admin_present_asks_suspense() -> None:
    qs = _follow_up_questions({"admin_watch_items": ["Claims pending"]})
    assert any("suspense" in q.lower() for q in qs)


# ---------------------------------------------------------------------------
# Full agent run
# ---------------------------------------------------------------------------

def test_agent_run_no_handoff_returns_low_confidence(agent: ChiefOfStaffAideAgent) -> None:
    resp = agent.run("What should I focus on?", _ctx())
    assert resp.confidence is Confidence.low


def test_agent_run_full_handoff_returns_medium_confidence(agent: ChiefOfStaffAideAgent) -> None:
    handoff = {
        "pme": ["EWS"],
        "fitreps": [{"occasion": "Annual", "due_date": "2026-10-01"}],
        "drill_dates": ["2026-09-06"],
        "admin_watch_items": ["Claims pending"],
    }
    resp = agent.run("What should I focus on?", _ctx(handoff))
    assert resp.confidence is Confidence.medium


def test_agent_run_no_handoff_questions_gap_filling(agent: ChiefOfStaffAideAgent) -> None:
    resp = agent.run("Brief me.", _ctx())
    qs = resp.follow_up_questions
    assert any("drill" in q.lower() for q in qs)
    assert any("pme" in q.lower() for q in qs)


def test_agent_run_with_drill_date_question_references_it(agent: ChiefOfStaffAideAgent) -> None:
    resp = agent.run("Brief me.", _ctx({"drill_dates": ["2026-09-06"]}))
    combined = " ".join(resp.follow_up_questions).lower()
    assert "2026-09-06" in combined or "drill" in combined


def test_agent_run_answer_includes_handoff_data(agent: ChiefOfStaffAideAgent) -> None:
    handoff = {"admin_watch_items": ["Unique-admin-token"]}
    resp = agent.run("What are my watch items?", _ctx(handoff))
    assert "Unique-admin-token" in resp.answer


def test_agent_run_answer_empty_sections_say_no_items(agent: ChiefOfStaffAideAgent) -> None:
    resp = agent.run("Brief me.", _ctx({}))
    assert "No PME watch items supplied" in resp.answer


def test_agent_run_non_dict_handoff_treated_as_empty(agent: ChiefOfStaffAideAgent) -> None:
    ctx = AgentContext(extra={"handoff": "garbage"})
    resp = agent.run("Brief me.", ctx)
    assert resp.confidence is Confidence.low
    assert "No PME watch items supplied" in resp.answer
