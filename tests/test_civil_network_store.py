from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.civil_network import (
    CivilEvidenceKind,
    CivilNetwork,
    CivilNetworkEvidence,
    CivilNetworkNode,
    CivilNetworkRelationship,
)
from app.services.staff.civil_network_store import CivilNetworkStore


def _evidence() -> CivilNetworkEvidence:
    return CivilNetworkEvidence(
        title="County emergency plan",
        url="https://example.test/emergency-plan",
        retrieved_at=date(2026, 7, 16),
        excerpt="The county coordinates emergency support.",
    )


def _network() -> CivilNetwork:
    county = CivilNetworkNode(id="county", kind="organization", display_name="County emergency management")
    hospital = CivilNetworkNode(id="hospital", kind="service", display_name="Regional hospital")
    relationship = CivilNetworkRelationship(
        from_node_id=county.id,
        to_node_id=hospital.id,
        kind="coordination",
        evidence_kind=CivilEvidenceKind.sourced_observation,
        description="Coordinates emergency support.",
        evidence=[_evidence()],
    )
    return CivilNetwork(
        title="Flood exercise",
        event_id="flood-26",
        purpose="G-9 coordination",
        nodes=[county, hospital],
        relationships=[relationship],
    )


def test_store_isolates_networks_by_owner_and_event(tmp_path: Path) -> None:
    store = CivilNetworkStore(tmp_path)
    saved = store.create("owner-a", _network())

    assert store.get("owner-a", saved.id).event_id == "flood-26"
    with pytest.raises(KeyError):
        store.get("owner-b", saved.id)


def test_public_role_holder_and_sourced_relationship_require_fields() -> None:
    with pytest.raises(ValidationError):
        CivilNetworkNode(kind="public_role_holder", display_name="Example official")
    with pytest.raises(ValidationError, match="evidence"):
        CivilNetworkRelationship(
            from_node_id="county",
            to_node_id="hospital",
            kind="coordination",
            evidence_kind="sourced_observation",
            description="Coordinates support.",
        )
    with pytest.raises(ValidationError, match="evidence"):
        CivilNetworkNode(
            kind="organization",
            display_name="County emergency management",
            evidence_kind="sourced_observation",
        )


def test_network_rejects_relationships_to_unknown_nodes() -> None:
    relationship = CivilNetworkRelationship(
        from_node_id="county",
        to_node_id="unknown",
        kind="dependency",
        evidence_kind="planning_hypothesis",
        description="Potential continuity concern.",
    )
    with pytest.raises(ValidationError, match="existing node"):
        CivilNetwork(
            title="Flood exercise",
            event_id="flood-26",
            purpose="G-9 coordination",
            nodes=[CivilNetworkNode(id="county", kind="organization", display_name="County")],
            relationships=[relationship],
        )


def test_snapshot_deep_copies_network_and_stays_unchanged_after_save(tmp_path: Path) -> None:
    store = CivilNetworkStore(tmp_path)
    saved = store.create("owner-a", _network())
    snapshot = store.snapshot("owner-a", saved.id, "MSEL v1")

    saved.title = "Updated flood exercise"
    store.save("owner-a", saved)

    reloaded = store.get("owner-a", saved.id)
    assert snapshot.network.title == "Flood exercise"
    assert reloaded.snapshots[0].network.title == "Flood exercise"
    assert reloaded.snapshots[0].snapshot_id == snapshot.snapshot_id


def test_second_snapshot_does_not_nest_prior_snapshots(tmp_path: Path) -> None:
    store = CivilNetworkStore(tmp_path)
    saved = store.create("owner-a", _network())

    first = store.snapshot("owner-a", saved.id, "MSEL v1")
    second = store.snapshot("owner-a", saved.id, "MSEL v2")

    reloaded = store.get("owner-a", saved.id)
    assert first.network.snapshots == []
    assert second.network.snapshots == []
    assert [snapshot.snapshot_id for snapshot in reloaded.snapshots] == [first.snapshot_id, second.snapshot_id]
