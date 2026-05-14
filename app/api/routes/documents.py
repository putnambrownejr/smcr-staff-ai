from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.documents import DocumentRead, IngestRequest, IngestResponse
from app.schemas.sources import validate_manifest

router = APIRouter(prefix="/documents", tags=["documents"])


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
