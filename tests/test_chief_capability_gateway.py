from pathlib import Path

import pytest

from app.schemas.chief_capabilities import ChiefCapabilityOperation, ChiefCapabilityRequest
from app.schemas.travel_cases import TravelCaseCreateRequest
from app.services.chief.capability_audit_store import CapabilityAuditStore
from app.services.chief.capability_gateway import ChiefCapabilityGateway
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.fitness.cadence_store import CadenceStore
from app.services.fitreps.store import FitrepStore


def _gateway(tmp_path: Path, repo_root: Path) -> ChiefCapabilityGateway:
    return ChiefCapabilityGateway(
        travel_store=TravelCaseStore(tmp_path / "travel"),
        fitrep_store=FitrepStore(tmp_path / "fitrep"),
        cadence_store=CadenceStore(tmp_path / "cadence"),
        audit_store=CapabilityAuditStore(tmp_path / "audit"),
        repository_root=repo_root,
    )


def test_gateway_appends_audits_and_undoes_once(tmp_path: Path) -> None:
    gateway = _gateway(tmp_path, tmp_path)
    trip = gateway.travel_store.create_case(TravelCaseCreateRequest(user_key="marine", title="AT"))
    response = gateway.execute(
        ChiefCapabilityRequest(
            user_key="marine",
            operation=ChiefCapabilityOperation.append_travel_ledger,
            payload={"trip_id": trip.trip_id, "description": "Taxi", "amount": "24.50"},
        )
    )
    assert response.changed is True
    assert response.undo_token
    assert gateway.summary("marine").travel_ledger_entry_count == 1
    assert gateway.undo("marine", response.undo_token).undone is True
    assert gateway.summary("marine").travel_ledger_entry_count == 0
    with pytest.raises(ValueError, match="already-used"):
        gateway.undo("marine", response.undo_token)


def test_gateway_summary_and_private_cadence_append(tmp_path: Path) -> None:
    gateway = _gateway(tmp_path, tmp_path)
    response = gateway.execute(
        ChiefCapabilityRequest(
            user_key="marine",
            operation=ChiefCapabilityOperation.append_cadence,
            payload={"title": "Mine", "text": "Move with purpose."},
        )
    )
    assert response.undo_token
    assert gateway.summary("marine").private_cadence_count == 1


def test_repository_search_is_root_scoped_and_excludes_projects(tmp_path: Path) -> None:
    (tmp_path / "safe.md").write_text("typed capability", encoding="utf-8")
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects" / "private.md").write_text("typed capability", encoding="utf-8")
    gateway = _gateway(tmp_path / "state", tmp_path)
    matches = gateway.search_repository("typed capability")
    assert [item["path"] for item in matches] == ["safe.md"]
    with pytest.raises(ValueError, match="repository root"):
        gateway.search_repository("typed", path="../")
    with pytest.raises(ValueError, match="excluded"):
        gateway.search_repository("typed", path="projects")
