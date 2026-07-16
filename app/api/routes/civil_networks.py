"""Owner-scoped lifecycle API for event civil-network datasets."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.agents import SourceSelection
from app.schemas.civil_network import CivilNetwork, CivilNetworkSnapshot
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.source_library.store import SourceLibraryStore
from app.services.staff.civil_network_service import CivilNetworkService
from app.services.staff.civil_network_store import CivilNetworkStore

router = APIRouter(prefix="/civil-networks", tags=["civil networks"], dependencies=[LocalApiKeyDependency])


class CivilNetworkWriteRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    network: CivilNetwork
    source_selection: SourceSelection | None = None
    include_noncurrent: bool = False


class CivilNetworkSnapshotRequest(BaseModel):
    user_key: str = Field(min_length=1, max_length=500)
    label: str = Field(min_length=1, max_length=500)


def get_civil_network_store() -> CivilNetworkStore:
    return CivilNetworkStore(get_settings().civil_network_storage_dir)


def get_civil_network_source_evidence_resolver() -> SourceEvidenceResolver:
    settings = get_settings()
    return SourceEvidenceResolver(SourceLibraryStore(settings.source_library_storage_dir))


def get_civil_network_service(
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
    source_evidence_resolver: Annotated[
        SourceEvidenceResolver, Depends(get_civil_network_source_evidence_resolver)
    ],
) -> CivilNetworkService:
    """Build a service from the same owner-scoped store used by each route."""
    return CivilNetworkService(store, source_evidence_resolver)


@router.post("", response_model=CivilNetwork)
def create_civil_network(
    request: CivilNetworkWriteRequest,
    service: Annotated[CivilNetworkService, Depends(get_civil_network_service)],
) -> CivilNetwork:
    return _save(request, service)


@router.get("", response_model=list[CivilNetwork])
def list_civil_networks(
    user_key: str,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
) -> list[CivilNetwork]:
    return store.list(user_key)


@router.get("/{network_id}", response_model=CivilNetwork)
def get_civil_network(
    network_id: str,
    user_key: str,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
) -> CivilNetwork:
    return _network_or_404(store, user_key, network_id)


@router.put("/{network_id}", response_model=CivilNetwork)
def update_civil_network(
    network_id: str,
    request: CivilNetworkWriteRequest,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
    service: Annotated[CivilNetworkService, Depends(get_civil_network_service)],
) -> CivilNetwork:
    _network_or_404(store, request.user_key, network_id)
    if request.network.id != network_id:
        raise HTTPException(status_code=422, detail="Civil-network id must match the request path.")
    return _save(request, service)


@router.delete("/{network_id}", status_code=204)
def delete_civil_network(
    network_id: str,
    user_key: str,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
) -> Response:
    _network_or_404(store, user_key, network_id)
    store.delete(user_key, network_id)
    return Response(status_code=204)


@router.post("/{network_id}/snapshots", response_model=CivilNetworkSnapshot)
def snapshot_civil_network(
    network_id: str,
    request: CivilNetworkSnapshotRequest,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
    service: Annotated[CivilNetworkService, Depends(get_civil_network_service)],
) -> CivilNetworkSnapshot:
    _network_or_404(store, request.user_key, network_id)
    try:
        return service.snapshot(request.user_key, network_id, request.label)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{network_id}/snapshots/{snapshot_id}", response_model=CivilNetworkSnapshot)
def get_civil_network_snapshot(
    network_id: str,
    snapshot_id: str,
    user_key: str,
    store: Annotated[CivilNetworkStore, Depends(get_civil_network_store)],
) -> CivilNetworkSnapshot:
    network = _network_or_404(store, user_key, network_id)
    for snapshot in network.snapshots:
        if snapshot.snapshot_id == snapshot_id:
            return snapshot
    raise HTTPException(status_code=404, detail="Civil-network snapshot was not found.")


def _save(request: CivilNetworkWriteRequest, service: CivilNetworkService) -> CivilNetwork:
    try:
        return service.create_or_update(
            request.user_key, request.network, request.source_selection, request.include_noncurrent
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _network_or_404(store: CivilNetworkStore, user_key: str, network_id: str) -> CivilNetwork:
    try:
        return store.get(user_key, network_id)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Civil network was not found.") from exc
