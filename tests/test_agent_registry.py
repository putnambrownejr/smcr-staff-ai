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
        "sel-enlisted-leader",
        "g9-civil-military",
        "medical-doc-advisor",
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
        "installation-practical-advisor",
        "pki-cac-troubleshooter",
        "leadership-advisor",
        "mcpp-planning-assistant",
        "opt-facilitator",
        "red-team-assumptions-challenge",
        "assessment-learning-advisor",
        "writing-briefing-coach",
        "joint-interagency-frame-advisor",
        "infantry-03xx-advisor",
        "osint-research-assistant",
        "terrain-map-advisor",
        "mos-adjutant-0102",
        "mos-intel-0202",
        "mos-logistics-0402",
        "mos-mobility-0430",
        "mos-supply-3002",
        "mos-magtf-planner-0511",
        "mos-commo",
        "mos-civil-affairs",
        "r2p2-planning-assistant",
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
    assert any(citation.title == "CIA World Factbook" for citation in response.structured_citations)
    assert response.source_trust


def test_s3_opso_agent_returns_staff_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("s3-opso")
    assert agent is not None

    response = agent.run("Help me shape a drill weekend synchronization plan.", context=AgentContext())

    assert "S-3 / OpsO advisory" in response.answer
    assert "TDG" in response.answer or "wargame" in response.answer.lower()
    assert response.structured_citations
    assert response.source_trust


def test_mcpp_agent_returns_deliberate_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("mcpp-planning-assistant")
    assert agent is not None

    response = agent.run("Help me run deliberate planning for a new training event.", context=AgentContext())

    assert "MCPP planning assistant advisory" in response.answer
    assert "COA wargaming" in response.answer
    assert response.structured_citations


def test_opt_facilitator_agent_returns_opt_conduct_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("opt-facilitator")
    assert agent is not None

    response = agent.run("Help me run mission analysis with my staff.", context=AgentContext())

    assert "OPT facilitator advisory" in response.answer
    assert "assumption log" in response.answer
    assert response.structured_citations


def test_red_team_agent_returns_assumptions_challenge_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("red-team-assumptions-challenge")
    assert agent is not None

    response = agent.run("Pressure-test this concept before we brief it.", context=AgentContext())

    assert "Red-team / assumptions challenge advisory" in response.answer
    assert "What to challenge" in response.answer
    assert response.structured_citations


def test_assessment_learning_agent_returns_aar_linkage_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("assessment-learning-advisor")
    assert agent is not None

    response = agent.run("Help me tie this event to the next drill's AAR follow-through.", context=AgentContext())

    assert "Assessment / learning advisory" in response.answer
    assert "Good AAR discipline" in response.answer
    assert response.structured_citations


def test_writing_briefing_agent_returns_product_discipline_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("writing-briefing-coach")
    assert agent is not None

    response = agent.run("Help me clean up this command brief.", context=AgentContext())

    assert "Writing / briefing coach advisory" in response.answer
    assert "Who is the audience?" in response.answer
    assert response.structured_citations


def test_joint_interagency_agent_returns_external_frame_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("joint-interagency-frame-advisor")
    assert agent is not None

    response = agent.run(
        "Help me widen the frame for a planning problem with outside stakeholders.",
        context=AgentContext(),
    )

    assert "Joint / interagency frame advisory" in response.answer
    assert "supported and who is supporting" in response.answer
    assert response.structured_citations


def test_r2p2_agent_returns_compressed_planning_guardrails() -> None:
    registry = AgentRegistry()
    agent = registry.get("r2p2-planning-assistant")
    assert agent is not None

    response = agent.run("Help me refine a familiar event under a short timeline.", context=AgentContext())

    assert "R2P2 planning assistant advisory" in response.answer
    assert "Abort compressed planning" in response.answer
    assert response.structured_citations


def test_mos_commo_agent_reads_as_s6_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-commo")
    assert agent is not None

    response = agent.run("Help me clean up a reserve comm plan.", context=AgentContext())

    assert "S-6 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_adjutant_agent_reads_as_s1_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-adjutant-0102")
    assert agent is not None

    response = agent.run("Help me tighten accountability and correspondence discipline.", context=AgentContext())

    assert "S-1 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_logistics_agent_reads_as_s4_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-logistics-0402")
    assert agent is not None

    response = agent.run("Help me clean up the logistics estimate for AT.", context=AgentContext())

    assert "S-4 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_supply_agent_reads_as_s4_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-supply-3002")
    assert agent is not None

    response = agent.run("Help me think through supply accountability before drill.", context=AgentContext())

    assert "S-4 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_intel_agent_reads_as_s2_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-intel-0202")
    assert agent is not None

    response = agent.run("Help me sharpen this estimate for a commander decision.", context=AgentContext())

    assert "S-2 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_magtf_planner_agent_reads_as_s3_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-magtf-planner-0511")
    assert agent is not None

    response = agent.run("Help me clean up mission analysis for this drill problem.", context=AgentContext())

    assert "S-3 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


def test_mos_civil_affairs_agent_reads_as_g9_subordinate_lane() -> None:
    registry = AgentRegistry()
    agent = registry.get("mos-civil-affairs")
    assert agent is not None

    response = agent.run("Help me preserve civil-affairs continuity between drills.", context=AgentContext())

    assert "G-9 lane" in response.answer
    assert "Relationship to the parent lane" in response.answer
    assert response.structured_citations


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
    assert "CommO" in response.answer or "operator lane" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_sel_agent_returns_ceremony_and_process_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("sel-enlisted-leader")
    assert agent is not None

    response = agent.run(
        "Help me think through a retirement ceremony, sequence, standards, and accountability checks.",
        context=AgentContext(),
    )

    assert "SEL / SgtMaj / 1stSgt advisory" in response.answer
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
    assert "civil-affairs MOS lane" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_mos_specialty_agents_are_grounded_under_parent_staff_lanes() -> None:
    registry = AgentRegistry()

    commo = registry.get("mos-commo")
    assert commo is not None
    commo_response = commo.run("Help me think through reserve comm readiness and rehearsals.", context=AgentContext())
    assert "under the S-6 lane" in commo_response.answer
    assert commo_response.structured_citations
    assert commo_response.source_trust

    civil_affairs = registry.get("mos-civil-affairs")
    assert civil_affairs is not None
    ca_response = civil_affairs.run(
        "Help me think through civil reconnaissance continuity for a reserve scenario.",
        context=AgentContext(),
    )
    assert "under the G-9 lane" in ca_response.answer
    assert ca_response.structured_citations
    assert ca_response.source_trust


def test_infantry_03xx_agent_returns_s3_family_training_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("infantry-03xx-advisor")
    assert agent is not None

    response = agent.run(
        "Help me shape a basic blank-fire urban familiarization lane for support Marines.",
        context=AgentContext(),
    )

    assert "Infantry / 03XX advisory draft under the S-3 family." in response.answer
    assert "familiarization" in response.answer.lower()
    assert response.structured_citations
    assert response.source_trust


def test_medical_doc_agent_returns_casevac_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("medical-doc-advisor")
    assert agent is not None

    response = agent.run(
        "Help me think through a training-safe CASEVAC and TCCC support plan.",
        context=AgentContext(),
    )

    assert "Medical / Doc advisory" in response.answer
    assert "CASEVAC" in response.answer
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

    assert "AirO exercise planning advisory" in response.answer
    assert "Supported aviation effect" in response.answer
    assert "Deconfliction and no-go questions" in response.answer
    assert response.structured_citations


def test_jag_agent_is_explicitly_non_authoritative() -> None:
    registry = AgentRegistry()
    agent = registry.get("jag-legal-advisor")
    assert agent is not None

    response = agent.run("What legal issue should I spot before routing this matter?", context=AgentContext())

    assert "not legal advice" in response.answer.lower()
    assert "SJA / military justice advisory" in response.answer
    assert "Exercise legal issue spotter" in response.answer
    assert "Legal review triggers" in response.answer
    assert any("Manual for Courts-Martial" in citation.title for citation in response.structured_citations)
    assert any("5800.16" in citation.title for citation in response.structured_citations)
    assert response.source_trust


def test_chaplain_agent_routes_to_real_support_channels() -> None:
    registry = AgentRegistry()
    agent = registry.get("chaplain-advisor")
    assert agent is not None

    response = agent.run("Help me think through a morale and welfare concern.", context=AgentContext())

    assert "Chaplain advisory" in response.answer
    assert response.source_trust


def test_leadership_agent_returns_historical_perspective_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("leadership-advisor")
    assert agent is not None

    response = agent.run(
        "Help me frame a PME on standards, moral courage, and command climate.",
        context=AgentContext(),
    )

    assert "Leadership / historical perspective advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_installation_agent_returns_practical_access_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("installation-practical-advisor")
    assert agent is not None

    response = agent.run("Help me think through visitor access for a command-sponsored event.", context=AgentContext())

    assert "Installation / base practical advisory" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_map_agent_returns_usgs_grounded_terrain_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("terrain-map-advisor")
    assert agent is not None

    response = agent.run(
        "Help me figure out what public topo and terrain products to pull for a training area near Miami.",
        context=AgentContext(),
    )

    assert "Terrain / map advisory" in response.answer
    assert any("USGS" in citation.title for citation in response.structured_citations)
    assert response.source_trust
