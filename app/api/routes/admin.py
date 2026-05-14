from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.admin import AdminReadinessResponse
from app.schemas.admin_workflows import AdminWorkflowRequest, AdminWorkflowResponse
from app.services.admin.readiness import AdminReadinessService
from app.services.admin.workflow_builder import AdminWorkflowBuilder
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/admin", tags=["admin readiness"], dependencies=[LocalApiKeyDependency])
_workflow_builder = AdminWorkflowBuilder()


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_admin_readiness_service(
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> AdminReadinessService:
    settings = get_settings()
    return AdminReadinessService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(context_store),
    )


@router.get("/readiness/{user_key}", response_model=AdminReadinessResponse)
def get_admin_readiness(
    user_key: str,
    service: Annotated[AdminReadinessService, Depends(get_admin_readiness_service)],
) -> AdminReadinessResponse:
    return service.build(user_key)


@router.post("/workflow", response_model=AdminWorkflowResponse)
def build_admin_workflow(request: AdminWorkflowRequest) -> AdminWorkflowResponse:
    return _workflow_builder.build(request)
