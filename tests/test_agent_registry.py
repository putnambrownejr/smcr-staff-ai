import pytest

from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry


@pytest.mark.parametrize(
    ("retired_id", "replacement_id"),
    [
        ("admin-readiness-advisor", "staff-s1"),
        ("correspondence-formatting", "staff-products"),
        ("doctrine-opord-assistant", "staff-products"),
        ("training-planner", "staff-opso"),
        ("fitrep-assistant", "staff-s1"),
        ("maradmin-monitor", "chief-of-staff"),
        ("joint-interagency-frame-advisor", "staff-opso"),
        # Agents consolidated into staff archetypes
        ("s1-admin-chief", "staff-s1"),
        ("s2-intel", "staff-s2"),
        ("s3-opso", "staff-opso"),
        ("s4-logistics", "staff-s4"),
        ("s6-comms", "staff-s6"),
        ("sel-enlisted-leader", "staff-sel"),
        ("medical-doc-advisor", "staff-surgeon"),
        ("airo-advisor", "ace"),
        ("jag-legal-advisor", "staff-sja"),
        ("chaplain-advisor", "staff-chaplain"),
        ("g9-civil-military", "staff-g9"),
        # MOS agents merged into staff archetypes
        ("mos-adjutant-0102", "staff-s1"),
        ("mos-intel-0202", "staff-s2"),
        ("mos-logistics-0402", "staff-s4"),
        ("mos-mobility-0430", "staff-s4"),
        ("mos-supply-3002", "staff-s4"),
        ("mos-magtf-planner-0511", "staff-opso"),
        ("mos-commo-0602", "staff-s6"),
        ("mos-commo", "staff-s6"),
        ("mos-jag-4402", "staff-sja"),
        ("mos-avso-7200", "ace"),
        ("mos-civil-affairs", "staff-g9"),
    ],
)
def test_retired_agents_are_not_registered_and_replacements_remain(
    retired_id: str,
    replacement_id: str,
) -> None:
    registry = AgentRegistry()

    assert registry.get(retired_id) is None
    assert registry.get(replacement_id) is not None


def test_agent_registry_loads_expected_agents() -> None:
    registry = AgentRegistry()
    ids = {metadata.id for metadata in registry.list_metadata()}

    assert {
        # Standalone utility agents
        "chief-of-staff",
        "planning-advisor",
        "red-team-assumptions-challenge",
        "assessment-learning-advisor",
        "writing-briefing-coach",
        "uniform-advisor",
        "drill-prep-calendar",
        "staff-products",
        "orm-risk-management",
        "installation-practical-advisor",
        "pki-cac-troubleshooter",
        "leadership-advisor",
        "infantry-tactics-advisor",
        "fires-advisor",
        "osint-research-assistant",
        "terrain-map-advisor",
        # MAGTF element agents
        "ace",
        "gce",
        "lce",
        # Consolidated staff archetypes
        "staff-xo",
        "staff-battle_captain",
        "staff-opso",
        "staff-s1",
        "staff-s2",
        "staff-s4",
        "staff-s6",
        "staff-sel",
        "staff-surgeon",
        "staff-sja",
        "staff-pao",
        "staff-chaplain",
        "staff-provost",
        "staff-ig",
        "staff-g8",
        "staff-g9",
    }.issubset(ids)


def test_staff_archetype_sensitive_input_gets_warning() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s6")
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


def test_staff_s1_returns_admin_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s1")
    assert agent is not None

    response = agent.run("Help me organize awards, DTS, and FitRep due-outs.", context=AgentContext())

    assert "S-1" in response.answer
    assert "Administration" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_s2_returns_estimate_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s2")
    assert agent is not None

    response = agent.run("Help me shape a public-source estimate for a staff question.", context=AgentContext())

    assert "S-2" in response.answer
    assert "Intelligence" in response.answer
    assert "OSINT" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_opso_returns_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-opso")
    assert agent is not None

    response = agent.run("Help me shape a drill weekend synchronization plan.", context=AgentContext())

    assert "OpsO" in response.answer or "S-3" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_s4_returns_logistics_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s4")
    assert agent is not None

    response = agent.run("Help me think through supportability for an AT movement plan.", context=AgentContext())

    assert "S-4" in response.answer
    assert "Logistics" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_s4_includes_merged_mos_depth() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s4")
    assert agent is not None

    response = agent.run("Check sustainment assumptions.", context=AgentContext())

    assert "0402" in response.answer
    assert "0430" in response.answer
    assert "3002" in response.answer


def test_staff_s6_returns_c2_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s6")
    assert agent is not None

    response = agent.run("Help me shape generic comm support for next drill.", context=AgentContext())

    assert "S-6" in response.answer
    assert "Communications" in response.answer
    assert "PACE" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_s6_includes_merged_mos_depth() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-s6")
    assert agent is not None

    response = agent.run("Check comms readiness.", context=AgentContext())

    assert "0602" in response.answer


def test_staff_sel_returns_standards_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-sel")
    assert agent is not None

    response = agent.run(
        "Help me think through a retirement ceremony, sequence, standards, and accountability checks.",
        context=AgentContext(),
    )

    assert "SgtMaj" in response.answer or "1stSgt" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_g9_returns_civil_military_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-g9")
    assert agent is not None

    response = agent.run(
        "Help me think through civil considerations and partner coordination for a reserve event.",
        context=AgentContext(),
    )

    assert "G-9" in response.answer
    assert "Civil" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_surgeon_returns_medical_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-surgeon")
    assert agent is not None

    response = agent.run(
        "Help me think through a training-safe CASEVAC and TCCC support plan.",
        context=AgentContext(),
    )

    assert "Surgeon" in response.answer or "Medical" in response.answer
    assert "CASEVAC" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_ace_agent_returns_planning_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("ace")
    assert agent is not None

    response = agent.run(
        "Help me think through generic air-support coordination for an exercise.",
        context=AgentContext(),
    )

    assert "ACE" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_ace_agent_includes_7200_depth() -> None:
    registry = AgentRegistry()
    agent = registry.get("ace")
    assert agent is not None

    response = agent.run("Check aviation support.", context=AgentContext())

    assert "7200" in response.answer


def test_gce_agent_returns_maneuver_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("gce")
    assert agent is not None

    response = agent.run(
        "Help me think through ground scheme of maneuver for a combined-arms exercise.",
        context=AgentContext(),
    )

    assert "GCE" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_lce_agent_returns_sustainment_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("lce")
    assert agent is not None

    response = agent.run(
        "Help me think through LCE sustainment and distribution support.",
        context=AgentContext(),
    )

    assert "LCE" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_staff_sja_is_explicitly_non_authoritative() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-sja")
    assert agent is not None

    response = agent.run("What legal issue should I spot before routing this matter?", context=AgentContext())

    assert "SJA" in response.answer
    assert "Legal" in response.answer
    assert "issue-spotting" in response.answer.lower() or "issue spotting" in response.answer.lower()
    assert response.structured_citations
    assert response.source_trust


def test_staff_sja_includes_merged_mos_depth() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-sja")
    assert agent is not None

    response = agent.run("Check legal routing.", context=AgentContext())

    assert "4402" in response.answer


def test_staff_chaplain_returns_support_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-chaplain")
    assert agent is not None

    response = agent.run("Help me think through a morale and welfare concern.", context=AgentContext())

    assert "Chaplain" in response.answer
    assert response.source_trust


def test_planning_advisor_covers_deliberate_rapid_and_opt_content() -> None:
    registry = AgentRegistry()
    agent = registry.get("planning-advisor")
    assert agent is not None

    response = agent.run("Help me run deliberate planning for a new training event.", context=AgentContext())

    assert "COA wargaming" in response.answer
    assert "Deliberate MCPP rhythm" in response.answer
    assert "assumption log" in response.answer
    assert "OPT lead" in response.answer
    assert "Compressed R2P2 rhythm" in response.answer
    assert "Abort compression" in response.answer
    assert response.structured_citations


def test_planning_advisor_reads_compressed_tempo_from_input() -> None:
    registry = AgentRegistry()
    agent = registry.get("planning-advisor")
    assert agent is not None

    rapid = agent.run("Help me refine a familiar event under a short timeline.", context=AgentContext())
    deliberate = agent.run("Help me plan a brand new problem from scratch.", context=AgentContext())

    assert "looks compressed" in rapid.answer
    assert "looks like deliberate planning" in deliberate.answer


def test_red_team_agent_returns_assumptions_challenge_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("red-team-assumptions-challenge")
    assert agent is not None

    response = agent.run("Pressure-test this concept before we brief it.", context=AgentContext())

    assert "Red-team / assumptions challenge advisory" in response.answer
    assert "What to challenge" in response.answer
    assert "Threat actor stereotype board" in response.answer
    assert "Red-cell questions" in response.answer
    assert response.structured_citations


def test_red_team_agent_inflects_to_urban_unrest_pattern() -> None:
    registry = AgentRegistry()
    agent = registry.get("red-team-assumptions-challenge")
    assert agent is not None

    response = agent.run(
        "Pressure-test this urban unrest scenario before we brief it.",
        context=AgentContext(request_is_training_or_fictional=True),
    )

    assert "urban_unrest" in response.answer
    assert "Crowd-shielded agitator" in response.answer


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


def test_infantry_tactics_agent_returns_s3_family_training_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("infantry-tactics-advisor")
    assert agent is not None

    response = agent.run(
        "Help me shape a basic blank-fire urban familiarization lane for support Marines.",
        context=AgentContext(),
    )

    assert "Infantry / 03XX advisory draft under the S-3 family." in response.answer
    assert "familiarization" in response.answer.lower()
    assert response.structured_citations
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


def test_echelon_adapts_in_staff_agent_output() -> None:
    registry = AgentRegistry()
    agent = registry.get("staff-opso")
    assert agent is not None

    bn_response = agent.run(
        "Vet this training concept.",
        context=AgentContext(extra={"echelon": "battalion"}),
    )
    div_response = agent.run(
        "Vet this training concept.",
        context=AgentContext(extra={"echelon": "division_group"}),
    )

    assert "battalion-level" in bn_response.answer
    assert "division/group-level" in div_response.answer


def test_fires_advisor_returns_fire_support_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("fires-advisor")
    assert agent is not None

    response = agent.run(
        "Help me shape a call-for-fire refresher for reserve artillery Marines.",
        context=AgentContext(),
    )

    assert "Fires" in response.answer
    assert "Fire Support" in response.answer
    assert response.structured_citations
    assert response.source_trust


def test_fires_advisor_includes_mos_depth() -> None:
    registry = AgentRegistry()
    agent = registry.get("fires-advisor")
    assert agent is not None

    response = agent.run("Check fire support readiness.", context=AgentContext())

    assert "0802" in response.answer
    assert "0861" in response.answer
    assert "FSCC" in response.answer


def test_fires_advisor_covers_broad_fires_function() -> None:
    registry = AgentRegistry()
    agent = registry.get("fires-advisor")
    assert agent is not None

    response = agent.run("What fires delivery means are available?", context=AgentContext())

    assert "NSFS" in response.answer
    assert "Mortars" in response.answer or "mortar" in response.answer.lower()
    assert "air-delivered" in response.answer.lower() or "Air-delivered" in response.answer
