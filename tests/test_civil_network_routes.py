from pathlib import Path

from fastapi.testclient import TestClient

import app.api.routes.civil_networks as civil_network_routes
from app.main import app
from app.services.staff.civil_network_store import CivilNetworkStore


def test_route_snapshot_is_owner_scoped(tmp_path: Path) -> None:
    app.dependency_overrides[civil_network_routes.get_civil_network_store] = lambda: CivilNetworkStore(tmp_path)
    client = TestClient(app)
    try:
        created = client.post("/civil-networks", json={"user_key": "owner-a", "network": _network_payload()})

        assert created.status_code == 200
        network_id = created.json()["id"]
        assert client.post(
            f"/civil-networks/{network_id}/snapshots", json={"user_key": "owner-a", "label": "MSEL v1"}
        ).status_code == 200
        assert client.get(f"/civil-networks/{network_id}", params={"user_key": "owner-b"}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_route_returns_422_for_invalid_manual_citation(tmp_path: Path) -> None:
    app.dependency_overrides[civil_network_routes.get_civil_network_store] = lambda: CivilNetworkStore(tmp_path)
    client = TestClient(app)
    payload = _network_payload()
    payload["nodes"] = [
        {
            "kind": "organization",
            "display_name": "County emergency management",
            "evidence_kind": "sourced_observation",
            "evidence": [
                {"title": "County plan", "retrieved_at": "2026-07-16", "excerpt": "Coordinates support."}
            ],
        }
    ]

    try:
        assert client.post("/civil-networks", json={"user_key": "owner-a", "network": payload}).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_route_lifecycle_and_owner_isolation(tmp_path: Path) -> None:
    app.dependency_overrides[civil_network_routes.get_civil_network_store] = lambda: CivilNetworkStore(tmp_path)
    client = TestClient(app)
    try:
        created = client.post("/civil-networks", json={"user_key": "owner-a", "network": _network_payload()})
        network = created.json()
        network["purpose"] = "Updated G-9 coordination"

        assert client.put(f"/civil-networks/{network['id']}", json={"user_key": "owner-a", "network": network}).status_code == 200
        assert client.get("/civil-networks", params={"user_key": "owner-a"}).status_code == 200
        assert client.put(f"/civil-networks/{network['id']}", json={"user_key": "owner-b", "network": network}).status_code == 404
        assert client.delete(f"/civil-networks/{network['id']}", params={"user_key": "owner-a"}).status_code == 204
        assert client.get(f"/civil-networks/{network['id']}", params={"user_key": "owner-a"}).status_code == 404
    finally:
        app.dependency_overrides.clear()


def _network_payload() -> dict[str, object]:
    return {"title": "Flood exercise", "event_id": "flood-26", "purpose": "G-9 coordination"}
