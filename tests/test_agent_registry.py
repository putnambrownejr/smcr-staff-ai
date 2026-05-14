from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


def test_agent_registry_loads_expected_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert {
        "admin-readiness-advisor",
        "s1-admin-chief",
        "s2-intel",
        "s3-opso",
        "s4-logistics",
        "s6-comms",
        "g9-civil-military",
        "airo-advisor",
        "jag-legal-advisor",
        "chaplain-advisor",
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


def test_s2_intel_agent_returns_estimate_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("s2-intel")
    assert agent is not None

    response = agent.run("Help me shape a public-source estimate for a staff question.", context=AgentContext())

    assert "S-2 advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_s3_opso_agent_returns_staff_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("s3-opso")
    assert agent is not None

    response = agent.run("Help me shape a drill weekend synchronization plan.", context=AgentContext())

    assert "S-3 / OpsO advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_s4_logistics_agent_returns_supportability_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("s4-logistics")
    assert agent is not None

    response = agent.run("Help me think through supportability for an AT movement plan.", context=AgentContext())

    assert "S-4 / logistics advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_s6_comms_agent_returns_c2_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("s6-comms")
    assert agent is not None

    response = agent.run("Help me shape generic comm support for next drill.", context=AgentContext())

    assert "S-6 advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_g9_agent_returns_civil_military_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("g9-civil-military")
    assert agent is not None

    response = agent.run(
        "Help me think through civil considerations and partner coordination for a reserve event.",
        context=AgentContext(),
    )

    assert "G-9 / civil-military advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_airo_agent_returns_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("airo-advisor")
    assert agent is not None

    response = agent.run(
        "Help me think through generic air-support coordination for an exercise.",
        context=AgentContext(),
    )

    assert "AirO advisory" in response.answer
    assert response.structured_citations


def test_jag_agent_is_explicitly_non_authoritative() -> None:
    registry = AgentRegistry()
    agent = registry.get("jag-legal-advisor")
    assert agent is not None

    response = agent.run("What legal issue should I spot before routing this matter?", context=AgentContext())

    assert "not legal advice" in response.answer.lower()
    assert response.source_trust


def test_chaplain_agent_routes_to_real_support_channels() -> None:
    registry = AgentRegistry()
    agent = registry.get("chaplain-advisor")
    assert agent is not None

    response = agent.run("Help me think through a morale and welfare concern.", context=AgentContext())

    assert "Chaplain advisory" in response.answer
    assert response.source_trust
