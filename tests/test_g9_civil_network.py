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
from app.schemas.staff import G9PlanningRequest
from app.services.staff.g9_planner import G9Planner


def _snapshot(trust_status: VerifiedSourceStatus = VerifiedSourceStatus.current) -> CivilNetworkSnapshot:
    evidence = CivilNetworkEvidence(
        title="Reviewed emergency plan",
        url="https://example.test/plan",
        retrieved_at=date(2026, 7, 16),
        trust_status=trust_status,
        excerpt="The public coordination forum meets weekly.",
        confidence="medium",
        review_state="reviewed",
    )
    observation = CivilNetworkNode(
        id="forum",
        kind=CivilNetworkNodeKind.forum,
        display_name="County coordination forum",
        evidence_kind=CivilEvidenceKind.sourced_observation,
        evidence=[evidence],
    )
    hypothesis = CivilNetworkNode(
        id="service",
        kind=CivilNetworkNodeKind.service,
        display_name="Shelter support service",
        evidence_kind=CivilEvidenceKind.planning_hypothesis,
    )
    return CivilNetworkSnapshot(
        label="MSEL v1",
        network=CivilNetwork(
            title="Flood exercise", event_id="flood-26", purpose="G-9 coordination", nodes=[observation, hypothesis]
        ),
    )


def test_g9_preserves_snapshot_evidence_labels_and_provenance() -> None:
    response = G9Planner().build(
        G9PlanningRequest(title="Flood", supported_problem="Coordinate support.", civil_network_snapshot=_snapshot())
    )

    assert any("Sourced observation" in line for line in response.civil_network_assessment)
    assert any("Planning hypothesis" in line for line in response.civil_network_assessment)
    assert any(item.source_label == "Reviewed emergency plan" for item in response.evidence_and_assumptions)
    assert "DRAFT — Verify all references against current official sources before acting." in response.warnings


def test_g9_warns_when_snapshot_evidence_is_noncurrent() -> None:
    response = G9Planner().build(
        G9PlanningRequest(
            title="Flood",
            supported_problem="Coordinate support.",
            civil_network_snapshot=_snapshot(VerifiedSourceStatus.watch),
        )
    )

    assert any("is watch; confirm before relying" in warning for warning in response.warnings)
