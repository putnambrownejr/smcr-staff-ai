from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.documents import DocumentRead, IngestRequest, IngestResponse
from app.schemas.ingestion import MessageRecord
from app.schemas.source_library import SavedSource, SourceFetchPreview, SourceRetrieveRequest, SourceRetrieveResponse
from app.schemas.source_state import SourceStateAcceptRequest, VerifiedSourceState
from app.schemas.source_updates import (
    DocumentationUpdateCandidate,
    DocumentationUpdateScanResult,
    DocumentationUpdateStatusUpdate,
    UpdateReviewStatus,
)
from app.schemas.source_verification import SourceVerificationRequest, SourceVerificationResponse
from app.schemas.sources import validate_manifest
from app.services.ingestion.document_update_monitor import DocumentUpdateMonitor
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.ingestion.source_state_service import SourceStateService
from app.services.ingestion.source_state_store import SourceStateStore
from app.services.ingestion.source_verifier import SourceVerifier, resolve_repo_local_path
from app.services.source_library.fetcher import PublicSourceFetcher, SourceFetchError
from app.services.source_library.service import (
    SourceLibraryFetchRequest,
    SourceLibraryPreviewRequest,
    SourceLibraryRecheckRequest,
    SourceLibraryReviewRequest,
    SourceLibraryService,
    SourceRecheckResult,
)
from app.services.source_library.store import SourceLibraryStore

router = APIRouter(prefix="/documents", tags=["documents"], dependencies=[LocalApiKeyDependency])


def get_update_store() -> DocumentUpdateStore:
    settings = get_settings()
    return DocumentUpdateStore(settings.document_updates_storage_dir)


def get_source_state_store() -> SourceStateStore:
    settings = get_settings()
    return SourceStateStore(settings.source_states_storage_dir)


def get_source_library_service() -> SourceLibraryService:
    settings = get_settings()
    return SourceLibraryService(
        SourceLibraryStore(settings.source_library_storage_dir),
        PublicSourceFetcher(max_bytes=settings.max_upload_bytes),
    )


def _source_library_error(exc: SourceFetchError) -> HTTPException:
    message = str(exc)
    if "approval" in message.lower():
        return HTTPException(status_code=409, detail=message)
    if "size limit" in message.lower() or "exceeds the configured size" in message.lower():
        return HTTPException(status_code=413, detail=message)
    if "HTML pages and direct PDF" in message:
        return HTTPException(status_code=415, detail=message)
    return HTTPException(status_code=422, detail=message)


@router.get(
    "",
    response_model=list[DocumentRead],
    response_description="Doctrine corpus ingestion is not yet wired; see ARCHITECTURE.md.",
)
def list_documents() -> list[DocumentRead]:
    return []


@router.post("/source-library/preview", response_model=SourceFetchPreview)
def preview_source_library_fetch(
    request: SourceLibraryPreviewRequest,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SourceFetchPreview:
    try:
        return service.preview(request)
    except SourceFetchError as exc:
        raise _source_library_error(exc) from exc


@router.post("/source-library/fetch", response_model=SavedSource)
def fetch_source_library_source(
    request: SourceLibraryFetchRequest,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SavedSource:
    try:
        return service.fetch(request)
    except SourceFetchError as exc:
        raise _source_library_error(exc) from exc


@router.get("/source-library", response_model=list[SavedSource])
def list_source_library_sources(
    user_key: str,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> list[SavedSource]:
    return service.list(user_key)


@router.post("/source-library/retrieve", response_model=SourceRetrieveResponse)
def retrieve_source_library_sources(
    request: SourceRetrieveRequest,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SourceRetrieveResponse:
    return service.retrieve(request)


@router.post("/source-library/{source_id}/recheck-preview", response_model=SourceFetchPreview)
def preview_source_library_recheck(
    source_id: str,
    user_key: str,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SourceFetchPreview:
    try:
        preview = service.recheck_preview(user_key, source_id)
    except SourceFetchError as exc:
        raise _source_library_error(exc) from exc
    if preview is None:
        raise HTTPException(status_code=404, detail=f"Unknown source-library source: {source_id}")
    return preview


@router.post("/source-library/{source_id}/recheck", response_model=SourceRecheckResult)
def recheck_source_library_source(
    source_id: str,
    request: SourceLibraryRecheckRequest,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SourceRecheckResult:
    if request.preview is None or request.approval is None:
        raise HTTPException(status_code=409, detail="A current recheck preview and acknowledgement are required.")
    try:
        result = service.recheck(source_id, request)
    except SourceFetchError as exc:
        raise _source_library_error(exc) from exc
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown source-library source: {source_id}")
    return result


@router.post("/source-library/{source_id}/review", response_model=SavedSource)
def review_source_library_source(
    source_id: str,
    request: SourceLibraryReviewRequest,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> SavedSource:
    try:
        source = service.review(source_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if source is None:
        raise HTTPException(status_code=404, detail=f"Unknown source-library source: {source_id}")
    return source


@router.delete("/source-library/{source_id}")
def remove_source_library_source(
    source_id: str,
    user_key: str,
    service: Annotated[SourceLibraryService, Depends(get_source_library_service)],
) -> dict[str, bool]:
    if not service.remove(user_key, source_id):
        raise HTTPException(status_code=404, detail=f"Unknown source-library source: {source_id}")
    return {"removed": True}


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    source = request.url or request.local_path or "configured source"
    manifest_validation = None
    documents_seen = 0
    if request.source_type == "manifest":
        local_path = resolve_repo_local_path(request.local_path or "")
        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"Manifest not found: {local_path}")
        manifest_validation = validate_manifest(local_path)
        documents_seen = manifest_validation.source_ref_count
        if manifest_validation.blocking_errors:
            raise HTTPException(status_code=422, detail=manifest_validation.blocking_errors)
    return IngestResponse(
        accepted=True,
        message=(
            f"Accepted {request.source_type} ingestion request for {source}. "
            "Prototype mode performs validation/dry-run only unless a concrete ingester is called."
        ),
        documents_seen=documents_seen,
        manifest_validation=manifest_validation,
    )


@router.post("/check-updates", response_model=DocumentationUpdateScanResult)
def check_document_updates(
    records: list[MessageRecord],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> DocumentationUpdateScanResult:
    result = DocumentUpdateMonitor().scan_maradmin_records(records)
    return DocumentationUpdateScanResult(
        candidates=update_store.save_many(result.candidates),
        warnings=result.warnings,
    )


@router.get("/updates", response_model=list[DocumentationUpdateCandidate])
def list_document_updates(
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
    status: UpdateReviewStatus | None = None,
) -> list[DocumentationUpdateCandidate]:
    return update_store.list(status=status)


@router.get("/source-states", response_model=list[VerifiedSourceState])
def list_source_states(
    source_state_store: Annotated[SourceStateStore, Depends(get_source_state_store)],
) -> list[VerifiedSourceState]:
    return source_state_store.list()


@router.post("/updates/{candidate_id}/status", response_model=DocumentationUpdateCandidate)
def update_document_update_status(
    candidate_id: str,
    update: DocumentationUpdateStatusUpdate,
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
) -> DocumentationUpdateCandidate:
    candidate = update_store.update_status(candidate_id, update)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {candidate_id}")
    return candidate


@router.post("/source-states/accept/{candidate_id}", response_model=VerifiedSourceState)
def accept_document_update_as_source_state(
    candidate_id: str,
    request: SourceStateAcceptRequest,
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
    source_state_store: Annotated[SourceStateStore, Depends(get_source_state_store)],
) -> VerifiedSourceState:
    state = SourceStateService(update_store, source_state_store).accept_candidate(candidate_id, request)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {candidate_id}")
    return state


@router.post("/verify-sources", response_model=SourceVerificationResponse)
def verify_sources(request: SourceVerificationRequest) -> SourceVerificationResponse:
    try:
        return SourceVerifier().verify(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
