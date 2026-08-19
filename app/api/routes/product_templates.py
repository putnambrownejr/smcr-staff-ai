from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.product_templates import (
    CreateManualProductTemplateRequest,
    CreateProductTemplateFromContextRequest,
    ProductTemplateListResponse,
    ProductTemplateRecord,
    SystemTemplateDetail,
    SystemTemplateListResponse,
)
from app.services.storage.local_context_store import LocalContextStore
from app.services.templates.product_template_repository import ProductTemplateRepository
from app.services.templates.system_template_catalog import SystemTemplateCatalog

REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = REPO_ROOT / "data" / "seed"

router = APIRouter(
    prefix="/product-templates",
    tags=["product templates"],
    dependencies=[LocalApiKeyDependency],
)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_template_repository() -> Iterator[ProductTemplateRepository]:
    settings = get_settings()
    yield ProductTemplateRepository(settings.product_template_storage_dir)


def get_system_template_catalog() -> SystemTemplateCatalog:
    return SystemTemplateCatalog.from_dir(SEED_DIR / "system_templates")


@router.post("/from-context", response_model=ProductTemplateRecord)
def create_product_template_from_context(
    request: CreateProductTemplateFromContextRequest,
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
    context_store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> ProductTemplateRecord:
    try:
        return repository.create_from_context(request, context_store)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/manual", response_model=ProductTemplateRecord)
def create_manual_product_template(
    request: CreateManualProductTemplateRequest,
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
) -> ProductTemplateRecord:
    return repository.create_manual(request)


@router.get("", response_model=ProductTemplateListResponse)
def list_product_templates(
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
) -> ProductTemplateListResponse:
    records = repository.list()
    by_type: dict[str, int] = {}
    for record in records:
        by_type[record.template_type.value] = by_type.get(record.template_type.value, 0) + 1
    return ProductTemplateListResponse(
        total_templates=len(records),
        by_type=by_type,
        records=records,
    )


@router.get("/system", response_model=SystemTemplateListResponse)
def list_system_product_templates(
    catalog: Annotated[SystemTemplateCatalog, Depends(get_system_template_catalog)],
) -> SystemTemplateListResponse:
    records = [catalog.get_detail(record.template_id) for record in catalog.list()]
    system_records = [record for record in records if record is not None]
    by_type: dict[str, int] = {}
    for record in system_records:
        by_type[record.template_type.value] = by_type.get(record.template_type.value, 0) + 1
    return SystemTemplateListResponse(
        total_templates=len(system_records),
        by_type=by_type,
        records=system_records,
    )


@router.get("/system/{template_id}", response_model=SystemTemplateDetail)
def get_system_product_template(
    template_id: str,
    catalog: Annotated[SystemTemplateCatalog, Depends(get_system_template_catalog)],
) -> SystemTemplateDetail:
    record = catalog.get_detail(template_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown system product template: {template_id}")
    return record


@router.get("/{template_id}", response_model=ProductTemplateRecord)
def get_product_template(
    template_id: str,
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
) -> ProductTemplateRecord:
    record = repository.get(template_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Unknown product template: {template_id}")
    return record


@router.delete("/{template_id}", status_code=204)
def delete_product_template(
    template_id: str,
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
) -> None:
    if not repository.delete(template_id):
        raise HTTPException(status_code=404, detail=f"Unknown product template: {template_id}")
