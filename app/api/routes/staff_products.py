from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.poam import PoamRequest, PoamResponse
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductDraftResponse
from app.services.staff_products.builder import StaffProductBuilder
from app.services.staff_products.poam_builder import PoamBuilder
from app.services.templates.product_template_repository import ProductTemplateRepository
from app.services.templates.system_template_catalog import SystemTemplateCatalog

router = APIRouter(prefix="/staff-products", tags=["staff products"], dependencies=[LocalApiKeyDependency])
REPO_ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = REPO_ROOT / "data" / "seed"

_builder = StaffProductBuilder()
_poam_builder = PoamBuilder()


def get_template_repository() -> Iterator[ProductTemplateRepository]:
    settings = get_settings()
    yield ProductTemplateRepository(settings.product_template_storage_dir)


def get_system_template_catalog() -> SystemTemplateCatalog:
    return SystemTemplateCatalog.from_dir(SEED_DIR / "system_templates")


@router.post("/draft", response_model=StaffProductDraftResponse)
def draft_staff_product(
    request: StaffProductDraftRequest,
    repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
    system_template_catalog: Annotated[SystemTemplateCatalog, Depends(get_system_template_catalog)],
) -> StaffProductDraftResponse:
    templates = []
    missing = []
    for template_id in request.template_ids:
        template = repository.get(template_id)
        if template is None:
            template = system_template_catalog.get(template_id)
        if template is None:
            missing.append(template_id)
        else:
            templates.append(template)
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown product template(s): {', '.join(missing)}")
    return _builder.build(request, templates=templates)


@router.post("/poam", response_model=PoamResponse)
def build_poam(request: PoamRequest) -> PoamResponse:
    return _poam_builder.build(request)
