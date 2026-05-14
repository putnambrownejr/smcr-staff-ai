from fastapi import APIRouter

from app.schemas.personnel import PersonnelProductRequest, PersonnelProductResponse
from app.services.personnel.product_builder import PersonnelProductBuilder

router = APIRouter(prefix="/personnel", tags=["personnel products"])
_builder = PersonnelProductBuilder()


@router.post("/products", response_model=PersonnelProductResponse)
def build_personnel_product(request: PersonnelProductRequest) -> PersonnelProductResponse:
    return _builder.build(request)
