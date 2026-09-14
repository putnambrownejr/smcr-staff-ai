"""Tests for the virtual staff round table endpoint."""

from __future__ import annotations

import json
import threading
from collections.abc import Generator
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Presets and generic questions (Sep 2026): the whole staff answers in one go
# ---------------------------------------------------------------------------

def test_xo_sits_at_every_auto_selected_table() -> None:
    participants, _ = resolve_participants(SCENARIO_INPUT, [], "chief-of-staff")
    assert participants[0] == "staff-xo"


def test_generic_question_falls_back_to_the_full_staff() -> None:
    participants, auto = resolve_participants("What should I do about this?", [], "chief-of-staff")
    assert "staff-s1" in participants
    assert "staff-sel" in participants
    assert "staff-g9" in participants
    assert "orm-risk-management" in participants
    assert "chief-of-staff" not in participants
    assert auto == participants


def test_training_question_pulls_the_training_seats_in_auto_mode() -> None:
    participants, auto = resolve_participants(
        "Plan a range day and land nav training event for next drill weekend.", [], "chief-of-staff"
    )
    assert "staff-opso" in auto
    assert "orm-risk-management" in auto
    assert "staff-xo" in participants


@pytest.mark.parametrize(
    ("preset", "must_include", "must_exclude"),
    [
        ("full_staff", {"staff-xo", "staff-s4", "staff-g8", "red-team-assumptions-challenge"}, set()),
        ("training", {"staff-opso", "orm-risk-management", "assessment-learning-advisor"}, {"staff-g8", "staff-pao"}),
        ("command_team", {"staff-xo", "staff-sel", "staff-sja", "staff-chaplain"}, {"staff-s4", "staff-s6"}),
    ],
)
def test_named_presets_seat_fixed_councils(preset: str, must_include: set[str], must_exclude: set[str]) -> None:
    participants, _ = resolve_participants("Anything at all.", [], "chief-of-staff", preset)
    assert must_include <= set(participants)
    assert not (must_exclude & set(participants))
    assert "chief-of-staff" not in participants


def test_roundtable_endpoint_full_staff_preset_answers_a_generic_training_question() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": "Help me build a two-day land navigation and patrolling drill for 60 Marines.",
            "preset": "full_staff",
            "rounds": 1,
            "context": {"request_is_training_or_fictional": True},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["participants"]) >= 16
    entries = data["rounds"][0]["entries"]
    assert {entry["agent_id"] for entry in entries} == set(data["participants"])
    assert all(entry["answer"].strip() for entry in entries)
    assert data["synthesis"]["agent_id"] == "chief-of-staff"
    # Local mode is labelled honestly: templates, no analysis.
    assert data["mode"] == "local_templates"
    assert data["warnings"][0].startswith("NO AI ANALYSIS WAS PERFORMED")


# ---------------------------------------------------------------------------
# Honest modes: capability, staff call packets, and external perspectives
# ---------------------------------------------------------------------------

def test_capability_reports_no_external_ai_when_unconfigured() -> None:
    response = TestClient(app).get("/agents/roundtable/capability")
    assert response.status_code == 200
    data = response.json()
    assert data["external_available"] is False
    assert "Nothing here can analyze your input" in data["note"]


def test_packet_organizes_seats_without_analysis() -> None:
    response = TestClient(app).post(
        "/agents/roundtable/packet",
        json={"scenario": "SITREP: land nav drill, 60 Marines, ammo pending.", "preset": "training"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "roundtable"
    assert "staff-opso" in data["participants"]
    assert data["synthesizer"] == "chief-of-staff"
    packet = data["packet_markdown"]
    assert "No AI has run and nothing below is analysis" in packet
    assert "## Your input" in packet and "ammo pending" in packet
    assert "## Instructions for the AI" in packet
    assert "### 1. OpsO / S-3 / G-3" in packet
    assert "Questions this seat always tests" in packet
    assert "Role notes (doctrine this seat works from)" in packet
    assert "## Synthesizer" in packet
    assert data["saved_doc_id"] is None
    assert "No AI analysis was performed" in data["note"]


def test_packet_can_omit_role_notes_and_build_chains() -> None:
    client = TestClient(app)
    slim = client.post(
        "/agents/roundtable/packet",
        json={"scenario": "Test.", "preset": "command_team", "include_role_notes": False},
    ).json()
    assert "Role notes (doctrine" not in slim["packet_markdown"]
    chain = client.post(
        "/agents/roundtable/packet",
        json={"scenario": "Test.", "kind": "chain", "agents": ["gce", "fires-advisor", "ace", "lce"]},
    ).json()
    assert chain["kind"] == "chain"
    assert chain["participants"] == ["gce", "fires-advisor", "ace", "lce"]
    assert "Run these agents **in order**" in chain["packet_markdown"]
    assert "## Synthesizer" not in chain["packet_markdown"]
    empty_chain = client.post("/agents/roundtable/packet", json={"scenario": "Test.", "kind": "chain"})
    assert empty_chain.status_code == 422


def test_packet_save_lands_in_drafted_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_DOCS_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        saved = client.post(
            "/agents/roundtable/packet",
            json={"scenario": "Test.", "preset": "command_team", "save": True, "user_key": "capt-packet"},
        )
        assert saved.status_code == 200, saved.text
        doc_id = saved.json()["saved_doc_id"]
        assert doc_id
        listed = client.get("/user-docs/generations/capt-packet").json()
        assert any(entry["id"] == doc_id and "Staff call packet" in entry["title"] for entry in listed)
        unsaved = client.post("/agents/roundtable/packet", json={"scenario": "Test.", "save": True})
        assert unsaved.status_code == 422
    finally:
        get_settings.cache_clear()


def test_local_roundtable_is_labelled_as_templates_not_analysis() -> None:
    response = TestClient(app).post(
        "/agents/roundtable",
        json={"scenario": "This is a test.", "agents": ["staff-s4"], "rounds": 1},
    )
    data = response.json()
    assert data["mode"] == "local_templates"
    assert data["warnings"][0].startswith("NO AI ANALYSIS WAS PERFORMED")


@patch("app.services.llm_client.generate_scenario_response")
def test_external_roundtable_convenes_every_seat_on_a_generic_question(mock_generate: MagicMock) -> None:
    def fake_generate(system_prompt: str, template: str, user_input: str, **kwargs: object) -> ScenarioGenerationResult:
        if "ROUND TABLE SYNTHESIS" in template:
            return _generated("Integrated picture", {"role": "cos_synthesis", "bottom_line": "Ammo is the long pole."})
        if "Logistics (LCE)" in template:
            return _generated("S-4 view", {"role": "s4", "summary": "Ammo request is late.", "key_concerns": ["ASP lead time"]})
        return _generated("Planning view", {"role": "planning_advisor", "summary": "Deliberate tempo."})

    mock_generate.side_effect = fake_generate
    response = TestClient(app).post(
        "/agents/roundtable",
        json={
            "scenario": "Plan a land nav drill for 60 Marines; ammo request not yet submitted.",
            "agents": ["staff-s4", "planning-advisor"],
            "rounds": 1,
            "inference": "external",
            "context": {"request_is_training_or_fictional": True},
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["mode"] == "external_ai"
    assert mock_generate.call_count == 3  # two seats + synthesis
    entries = {entry["agent_id"]: entry for entry in data["rounds"][0]["entries"]}
    assert entries["staff-s4"]["scenario_output_status"] == "validated"
    notice = "DRAFT — Verify all references against current official sources before acting."
    assert entries["staff-s4"]["answer"] == "S-4 view\n\n" + notice
    assert all(notice in entry["answer"] for entry in entries.values())
    assert notice in data["synthesis"]["answer"]
    assert data["assessments"]["s4"]["key_concerns"] == ["ASP lead time"]
    assert data["synthesis"]["scenario_output"]["role"] == "cos_synthesis"
    assert not any(w.startswith("NO AI ANALYSIS") for w in data["warnings"])
    # The seat's template was sent as its lens, not as the answer.
    lens_template = next(call.args[1] for call in mock_generate.call_args_list if "Logistics (LCE)" in call.args[1])
    assert "STAFF PERSPECTIVE" in lens_template and "Concerns to test:" in lens_template


def test_single_agent_external_inference_without_a_key_says_so() -> None:
    response = TestClient(app).post(
        "/agents/staff-s4/run",
        json={"input": "Plan sustainment for a drill.", "options": {"inference": "external"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output_status"] == "template_only"
    assert "local deterministic template" in data["answer"]
