from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


def test_agent_registry_loads_expected_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert {
        "maradmin-monitor",
        "uniform-advisor",
        "drill-prep-calendar",
        "doctrine-opord-assistant",
        "training-planner",
        "orm-risk-management",
        "fitrep-assistant",
        "leadership-advisor",
        "osint-research-assistant",
        "mos-commo",
        "mos-civil-affairs",
    }.issubset(ids)


def test_agent_sensitive_input_gets_warning() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-commo")
    assert agent is not None

    response = agent.run("Use frequency 123.45 MHz and COMSEC keymat", context=AgentContext())

    assert response.confidence == "low"
    assert any("sensitive" in warning.lower() for warning in response.warnings)
