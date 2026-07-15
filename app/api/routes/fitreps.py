from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.fitreps import (
    FitrepAnalyticsResponse,
    FitrepImportConfirmRequest,
    FitrepImportKind,
    FitrepImportPreviewRequest,
    FitrepImportProposal,
    FitrepImprovementGoal,
    FitrepImprovementGoalRequest,
    FitrepReport,
    FitrepReportCreateRequest,
    FitrepWorkspace,
    RsProfileSnapshot,
    RsProfileSnapshotCreateRequest,
)
from app.services.fitreps.analytics import build_fitrep_analytics
from app.services.fitreps.importer import propose_report_import, propose_rs_profile_import
from app.services.fitreps.store import FitrepStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/fitreps", tags=["fitreps"], dependencies=[LocalApiKeyDependency])


def get_fitrep_store() -> Iterator[FitrepStore]:
    yield FitrepStore(get_settings().fitrep_storage_dir)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


@router.get("/{user_key}", response_model=FitrepWorkspace)
def get_fitrep_workspace(
    user_key: str, store: Annotated[FitrepStore, Depends(get_fitrep_store)]
) -> FitrepWorkspace:
    return store.get(user_key)


@router.post("/{user_key}/reports", response_model=FitrepReport, status_code=201)
def add_fitrep_report(
    user_key: str,
    request: FitrepReportCreateRequest,
    store: Annotated[FitrepStore, Depends(get_fitrep_store)],
) -> FitrepReport:
    _matching_user_key(user_key, request.user_key)
    return store.add_report(request)


@router.post("/{user_key}/rs-profiles", response_model=RsProfileSnapshot, status_code=201)
def add_rs_profile(
    user_key: str,
    request: RsProfileSnapshotCreateRequest,
    store: Annotated[FitrepStore, Depends(get_fitrep_store)],
) -> RsProfileSnapshot:
    _matching_user_key(user_key, request.user_key)
    return store.add_rs_snapshot(request)


@router.post("/{user_key}/goals", response_model=FitrepImprovementGoal)
def upsert_fitrep_goal(
    user_key: str,
    request: FitrepImprovementGoalRequest,
    store: Annotated[FitrepStore, Depends(get_fitrep_store)],
) -> FitrepImprovementGoal:
    _matching_user_key(user_key, request.user_key)
    return store.upsert_goal(request)


@router.post("/{user_key}/imports/preview", response_model=FitrepImportProposal)
def preview_fitrep_import(
    user_key: str,
    request: FitrepImportPreviewRequest,
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> FitrepImportProposal:
    _matching_user_key(user_key, request.user_key)
    preview = context_store.read_preview(request.context_id)
    if preview is None:
        raise HTTPException(status_code=404, detail=f"Unknown local context item: {request.context_id}")
    if request.kind is FitrepImportKind.rs_profile:
        return propose_rs_profile_import(preview, request.context_id, user_key)
    return propose_report_import(preview, request.context_id, user_key)


@router.post("/{user_key}/imports/confirm", response_model=FitrepWorkspace, status_code=201)
def confirm_fitrep_import(
    user_key: str,
    request: FitrepImportConfirmRequest,
    store: Annotated[FitrepStore, Depends(get_fitrep_store)],
) -> FitrepWorkspace:
    _matching_user_key(user_key, request.user_key)
    if request.proposal.kind != request.kind:
        raise HTTPException(status_code=400, detail="Import kind and proposal kind must match.")
    if request.kind is FitrepImportKind.my_record and request.proposal.report is not None:
        _matching_user_key(user_key, request.proposal.report.user_key)
        store.add_report(request.proposal.report)
    elif request.kind is FitrepImportKind.rs_profile and request.proposal.rs_profile is not None:
        _matching_user_key(user_key, request.proposal.rs_profile.user_key)
        store.add_rs_snapshot(request.proposal.rs_profile)
    else:
        raise HTTPException(status_code=400, detail="The confirmed proposal has no matching record.")
    return store.get(user_key)


@router.get("/{user_key}/analytics", response_model=FitrepAnalyticsResponse)
def get_fitrep_analytics(
    user_key: str, store: Annotated[FitrepStore, Depends(get_fitrep_store)]
) -> FitrepAnalyticsResponse:
    return build_fitrep_analytics(store.get(user_key))


def _matching_user_key(path_user_key: str, body_user_key: str) -> None:
    if path_user_key != body_user_key:
        raise HTTPException(status_code=400, detail="user_key in path and body must match.")
