from datetime import date

from fastapi.testclient import TestClient

from app.api.routes import civil_networks
from app.main import app
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.source_library.store import SourceLibraryStore
from app.services.staff.civil_network_store import CivilNetworkStore


def _network_payload() -> dict[str, object]:
    evidence = {
        "title": "Reviewed emergency plan",
        "url": "https://example.test/plan",
        "retrieved_at": date(2026, 7, 16).isoformat(),
        "trust_status": "current",
        "excerpt": "The public coordination forum meets weekly.",
        "confidence": "medium",
        "review_state": "reviewed",
    }
    return {
        "title": "Flood exercise",
        "event_id": "flood-26",
        "purpose": "G-9 coordination",
        "nodes": [
            {
                "id": "forum",
                "kind": "forum",
                "display_name": "County coordination forum",
                "evidence_kind": "sourced_observation",
                "evidence": [evidence],
                "confidence": "medium",
                "review_state": "reviewed",
            },
            {
                "id": "shelter",
                "kind": "service",
                "display_name": "Shelter support service",
                "evidence_kind": "analytic_inference",
                "evidence": [
                    {
                        "title": "Planning note",
                        "bibliographic_note": "Exercise planning note",
                        "retrieved_at": date(2026, 7, 16).isoformat(),
                        "excerpt": "The forum may need shelter coordination.",
                        "confidence": "low",
                        "review_state": "reviewed",
                        "rationale": "Planning inference only.",
                    }
                ],
                "confidence": "low",
                "review_state": "reviewed",
            },
            {
                "id": "official",
                "kind": "public_role_holder",
                "display_name": "Public emergency-management director",
                "public_role": "Emergency-management director",
                "organization": "County emergency management",
                "event_relevance": "Coordinates the exercise's public emergency-management forum.",
                "evidence_kind": "sourced_observation",
                "evidence": [evidence],
                "confidence": "medium",
                "review_state": "reviewed",
            },
        ],
        "relationships": [
            {
                "id": "forum-coordinates-shelter",
                "from_node_id": "forum",
                "to_node_id": "shelter",
                "kind": "coordination",
                "evidence_kind": "sourced_observation",
                "description": "The public forum coordinates shelter-support discussion.",
                "evidence": [evidence],
                "confidence": "medium",
                "review_state": "reviewed",
            }
        ],
    }


def test_snapshot_preserves_provenance_through_g9_handoff(tmp_path) -> None:  # type: ignore[no-untyped-def]
    network_store = CivilNetworkStore(tmp_path / "networks")
    source_store = SourceLibraryStore(tmp_path / "sources")
    app.dependency_overrides[civil_networks.get_civil_network_store] = lambda: network_store
    app.dependency_overrides[civil_networks.get_civil_network_source_evidence_resolver] = (
        lambda: SourceEvidenceResolver(source_store)
    )
    client = TestClient(app)
    try:
        created = client.post("/civil-networks", json={"user_key": "owner", "network": _network_payload()})
        assert created.status_code == 200
        network = created.json()
        snapshot = client.post(
            f"/civil-networks/{network['id']}/snapshots", json={"user_key": "owner", "label": "MSEL v1"}
        )
        assert snapshot.status_code == 200
        snapshot_body = snapshot.json()
        assert snapshot_body["network"]["nodes"][2]["public_role"] == "Emergency-management director"
        assert snapshot_body["network"]["relationships"][0]["evidence"][0]["title"] == "Reviewed emergency plan"

        g9 = client.post(
            "/staff/g9-plan",
            json={
                "title": "Flood",
                "supported_problem": "Coordinate support.",
                "civil_network_snapshot": snapshot_body,
            },
        )
        assert g9.status_code == 200
        body = g9.json()
        assert any(item["source_label"] == "Reviewed emergency plan" for item in body["evidence_and_assumptions"])
        assert "DRAFT — Verify all references against current official sources before acting." in body["warnings"]
    finally:
        app.dependency_overrides.clear()
