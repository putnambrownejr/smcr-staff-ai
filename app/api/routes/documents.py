from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.documents import DocumentRead, IngestRequest, IngestResponse
from app.schemas.ingestion import MessageRecord
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
from app.services.ingestion.source_verifier import SourceVerifier

router = APIRouter(prefix="/documents", tags=["documents"])
_update_store = DocumentUpdateStore()
_source_state_store = SourceStateStore()


@router.get("", response_model=list[DocumentRead])
def list_documents() -> list[DocumentRead]:
    return [
        DocumentRead(
            source_id="example-doctrine-manifest",
            title="Doctrine corpus manifest placeholder",
            publication_type="manifest",
            issuing_org="smcr-staff-ai",
            retrieved_at=datetime.utcnow(),
            classification_label="UNCLASSIFIED",
            cui_flag=False,
        )
    ]


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest) -> IngestResponse:
    source = request.url or request.local_path or "configured source"
    manifest_validation = None
    documents_seen = 0
    if request.source_type == "manifest":
        local_path = Path(request.local_path or "")
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
def check_document_updates(records: list[MessageRecord]) -> DocumentationUpdateScanResult:
    result = DocumentUpdateMonitor().scan_maradmin_records(records)
    return DocumentationUpdateScanResult(
        candidates=_update_store.save_many(result.candidates),
        warnings=result.warnings,
    )


@router.get("/updates", response_model=list[DocumentationUpdateCandidate])
def list_document_updates(status: UpdateReviewStatus | None = None) -> list[DocumentationUpdateCandidate]:
    return _update_store.list(status=status)


@router.get("/source-states", response_model=list[VerifiedSourceState])
def list_source_states() -> list[VerifiedSourceState]:
    return _source_state_store.list()


@router.post("/updates/{candidate_id}/status", response_model=DocumentationUpdateCandidate)
def update_document_update_status(
    candidate_id: str,
    update: DocumentationUpdateStatusUpdate,
) -> DocumentationUpdateCandidate:
    candidate = _update_store.update_status(candidate_id, update)
    if candidate is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {candidate_id}")
    return candidate


@router.post("/source-states/accept/{candidate_id}", response_model=VerifiedSourceState)
def accept_document_update_as_source_state(
    candidate_id: str,
    request: SourceStateAcceptRequest,
) -> VerifiedSourceState:
    state = SourceStateService(_update_store, _source_state_store).accept_candidate(candidate_id, request)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown documentation update candidate: {candidate_id}")
    return state


@router.post("/verify-sources", response_model=SourceVerificationResponse)
def verify_sources(request: SourceVerificationRequest) -> SourceVerificationResponse:
    try:
        return SourceVerifier().verify(request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
