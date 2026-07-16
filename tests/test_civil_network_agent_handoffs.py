from datetime import date

from app.schemas.civil_network import (
    CivilEvidenceKind,
    CivilNetwork,
    CivilNetworkEvidence,
    CivilNetworkNode,
    CivilNetworkNodeKind,
    CivilNetworkSnapshot,
)
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.actor_network_agent import build_actor_network_agent
from app.services.agents.area_study_agent import build_area_study_agent
from app.services.agents.base import AgentContext
from app.services.agents.information_requirements_agent import build_information_requirements_agent
from app.services.agents.ipb_agent import build_ipb_assistant_agent
from app.services.agents.red_team_agent import build_red_team_agent


def _context() -> AgentContext:
    evidence = CivilNetworkEvidence(
        title="Public plan",
        url="https://example.test/plan",
        retrieved_at=date(2026, 7, 16),
        trust_status=VerifiedSourceStatus.watch,
        excerpt="A public coordination forum is listed.",
        confidence="low",
        review_state="reviewed",
    )
    snapshot = CivilNetworkSnapshot(
        label="Exercise snapshot",
        network=CivilNetwork(
            title="Flood",
            event_id="flood-26",
            purpose="Exercise planning",
            nodes=[
                CivilNetworkNode(
                    id="forum",
                    kind=CivilNetworkNodeKind.forum,
                    display_name="County forum",
                    evidence_kind=CivilEvidenceKind.sourced_observation,
                    evidence=[evidence],
                ),
                CivilNetworkNode(
                    id="inference",
                    kind=CivilNetworkNodeKind.organization,
                    display_name="Volunteer coordination organization",
                    evidence_kind=CivilEvidenceKind.analytic_inference,
                ),
                CivilNetworkNode(
                    id="service",
                    kind=CivilNetworkNodeKind.service,
                    display_name="Shelter service",
                    evidence_kind=CivilEvidenceKind.planning_hypothesis,
                ),
            ],
        ),
    )
    return AgentContext(extra={"civil_network_snapshot": snapshot.model_dump(mode="json")})


def test_agents_keep_snapshot_observations_hypotheses_and_warnings_distinct() -> None:
    for agent in (
        build_actor_network_agent(),
        build_area_study_agent(),
        build_information_requirements_agent(),
        build_ipb_assistant_agent(),
        build_red_team_agent(),
    ):
        response = agent.run("Assess the exercise.", _context())

        assert "Sourced observations:" in response.answer
        assert "Analytic inferences:" in response.answer
        assert "Volunteer coordination organization" in response.answer
        assert "Planning hypotheses:" in response.answer
        assert "trust status is watch" in response.answer
        assert response.answer.endswith("DRAFT — Verify all references against current official sources before acting.")
