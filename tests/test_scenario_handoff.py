"""Tests for structured JSON handoffs between staff agents."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.scenario_handoff import (
    ChainRequest,
    ChainStep,
    CoSScenarioOutput,
    G9ScenarioOutput,
    PlanningScenarioOutput,
    S2ScenarioOutput,
    S4ScenarioOutput,
    S6ScenarioOutput,
)
from app.services.agents.base import AgentContext


SCENARIO_INPUT = (
    "A magnitude 7.2 earthquake has struck the Philippines, affecting Manila and surrounding "
    "provinces. Estimated 500 casualties, 50,000 displaced. The airport is partially operational. "
    "A MEU is positioned nearby for potential FHADR response."
)

NON_SCENARIO_INPUT = "What is the process for building a training schedule?"


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_g9_scenario_output_schema():
    output = G9ScenarioOutput(role="g9")
    dumped = output.model_dump()
    assert dumped["role"] == "g9"
    assert "civil_situation" in dumped
    assert "ascope" in dumped
    assert "interagency" in dumped


def test_s2_scenario_output_schema():
    output = S2ScenarioOutput(role="s2")
    dumped = output.model_dump()
    assert dumped["role"] == "s2"
    assert "threat" in dumped
    assert "intel_gaps" in dumped


def test_planning_scenario_output_schema():
    output = PlanningScenarioOutput(role="planning", tempo="MCPP (deliberate)")
    dumped = output.model_dump()
    assert dumped["tempo"] == "MCPP (deliberate)"
    assert "mission_analysis" in dumped
    assert "tasks" in dumped


def test_cos_scenario_output_schema():
    output = CoSScenarioOutput(role="cos")
    dumped = output.model_dump()
    assert dumped["role"] == "cos"
    assert "staff_tasking" in dumped
    assert "decision_points" in dumped


# ---------------------------------------------------------------------------
# Agent scenario_output field
# ---------------------------------------------------------------------------

def test_g9_agent_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/staff-g9/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "g9"
    assert "civil_situation" in data["scenario_output"]


def test_s2_agent_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/staff-s2/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "s2"


def test_s4_agent_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/staff-s4/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "s4"


def test_s6_agent_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/staff-s6/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "s6"


def test_planning_advisor_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/planning-advisor/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "planning"
    assert "tempo" in data["scenario_output"]


def test_cos_agent_returns_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/chief-of-staff/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is not None
    assert data["scenario_output"]["role"] == "cos"


def test_non_scenario_returns_null_scenario_output():
    client = TestClient(app)
    response = client.post(
        "/agents/staff-g9/run",
        json={"input": NON_SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is None


def test_xo_non_scenario_returns_null_scenario_output():
    """XO has no scenario template, so even scenario input produces null."""
    client = TestClient(app)
    response = client.post(
        "/agents/staff-xo/run",
        json={"input": SCENARIO_INPUT, "context": {"request_is_training_or_fictional": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_output"] is None


# ---------------------------------------------------------------------------
# Prior assessments in context
# ---------------------------------------------------------------------------

def test_prior_assessments_in_context():
    ctx = AgentContext(
        prior_assessments={
            "g9": G9ScenarioOutput(role="g9").model_dump(),
        },
    )
    assert "g9" in ctx.prior_assessments
    assert ctx.prior_assessments["g9"]["role"] == "g9"


def test_agent_with_prior_assessments():
    client = TestClient(app)
    g9_output = G9ScenarioOutput(role="g9").model_dump()
    response = client.post(
        "/agents/staff-s2/run",
        json={
            "input": SCENARIO_INPUT,
            "context": {
                "request_is_training_or_fictional": True,
                "prior_assessments": {"g9": g9_output},
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "PRIOR STAFF ASSESSMENTS" in data["answer"]


# ---------------------------------------------------------------------------
# Chain endpoint
# ---------------------------------------------------------------------------

def test_chain_endpoint_basic():
    client = TestClient(app)
    response = client.post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [
                {"agent_id": "staff-g9"},
                {"agent_id": "staff-s2"},
            ],
            "context": {"request_is_training_or_fictional": True},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == SCENARIO_INPUT
    assert len(data["results"]) == 2
    assert data["results"][0]["agent_id"] == "staff-g9"
    assert data["results"][0]["scenario_output"] is not None
    assert data["results"][0]["scenario_output"]["role"] == "g9"
    assert data["results"][1]["agent_id"] == "staff-s2"
    assert data["results"][1]["scenario_output"] is not None
    assert data["results"][1]["scenario_output"]["role"] == "s2"


def test_chain_endpoint_passes_prior_assessments():
    client = TestClient(app)
    response = client.post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [
                {"agent_id": "staff-g9"},
                {"agent_id": "staff-s2"},
                {"agent_id": "planning-advisor"},
            ],
            "context": {"request_is_training_or_fictional": True},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3
    planning_answer = data["results"][2]["response"]["answer"]
    assert "PRIOR STAFF ASSESSMENTS" in planning_answer


def test_chain_endpoint_full_sequence():
    client = TestClient(app)
    response = client.post(
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
    assert len(data["results"]) == 4
    for result in data["results"]:
        assert result["scenario_output"] is not None


def test_chain_endpoint_unknown_agent():
    client = TestClient(app)
    response = client.post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [{"agent_id": "nonexistent-agent"}],
            "context": {},
        },
    )
    assert response.status_code == 404


def test_chain_endpoint_custom_step_input():
    client = TestClient(app)
    response = client.post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [
                {"agent_id": "staff-g9"},
                {"agent_id": "staff-s4", "input": SCENARIO_INPUT + " Focus on port logistics."},
            ],
            "context": {"request_is_training_or_fictional": True},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2


def test_chain_with_non_scenario_agent_produces_null_output():
    """Agents without scenario templates still work in chain but produce null output."""
    client = TestClient(app)
    response = client.post(
        "/agents/chain",
        json={
            "scenario": SCENARIO_INPUT,
            "steps": [
                {"agent_id": "staff-g9"},
                {"agent_id": "staff-xo"},
            ],
            "context": {"request_is_training_or_fictional": True},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["scenario_output"] is not None
    assert data["results"][1]["scenario_output"] is None
