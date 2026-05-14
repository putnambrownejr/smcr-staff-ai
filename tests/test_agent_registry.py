from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


def test_agent_registry_loads_expected_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert {
        "admin-readiness-advisor",
        "s1-admin-chief",
        "maradmin-monitor",
        "correspondence-formatting",
        "uniform-advisor",
        "drill-prep-calendar",
        "doctrine-opord-assistant",
        "staff-products",
        "training-planner",
        "orm-risk-management",
        "fitrep-assistant",
        "pki-cac-troubleshooter",
        "leadership-advisor",
        "osint-research-assistant",
        "mos-commo",
        "mos-civil-affairs",
    }.issubset(ids)


def test_correspondence_formatting_agent_returns_source_citations() -> None:
    registry = AgentRegistry()
    agent = registry.get("correspondence-formatting")
    assert agent is not None

    response = agent.run("Give me a naval letter formatting checklist.", context=AgentContext())

    assert "Correspondence formatting" in response.answer
    assert response.structured_citations
    assert any("5216" in citation.title for citation in response.structured_citations)


def test_agent_sensitive_input_gets_warning() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-commo")
    assert agent is not None

    response = agent.run("Use frequency 123.45 MHz and COMSEC keymat", context=AgentContext())

    assert response.confidence == "low"
    assert any("sensitive" in warning.lower() for warning in response.warnings)


def test_staff_products_agent_builds_scaffold() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-products")
    assert agent is not None

    response = agent.run("Build a training-only AAR for a drill admin process.", context=AgentContext())

    assert "AAR" in response.answer
    assert response.structured_citations
    assert any("human review" in warning.lower() for warning in response.warnings)


def test_pki_agent_returns_troubleshooting_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("pki-cac-troubleshooter")
    assert agent is not None

    response = agent.run("Chrome sees the CAC but MarineNet never prompts for a certificate.", context=AgentContext())

    assert "PKI/CAC troubleshooting advisory" in response.answer
    assert "Immediate checks" in response.answer
    assert response.structured_citations


def test_s1_admin_chief_agent_returns_source_trust_markers() -> None:
    registry = AgentRegistry()
    agent = registry.get("s1-admin-chief")
    assert agent is not None

    response = agent.run("Help me organize awards, DTS, and FitRep due-outs.", context=AgentContext())

    assert "S-1 / Admin chief advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust
