from fastapi import APIRouter

from app.schemas.personnel import (
    CorrespondenceConversionRequest,
    CorrespondenceConversionResponse,
    PersonnelProductRequest,
    PersonnelProductResponse,
)
from app.services.personnel.correspondence_converter import CorrespondenceConverter
from app.services.personnel.product_builder import PersonnelProductBuilder

router = APIRouter(prefix="/personnel", tags=["personnel products"])
_builder = PersonnelProductBuilder()
_converter = CorrespondenceConverter()


@router.post("/products", response_model=PersonnelProductResponse)
def build_personnel_product(request: PersonnelProductRequest) -> PersonnelProductResponse:
    return _builder.build(request)


@router.post("/convert-correspondence", response_model=CorrespondenceConversionResponse)
def convert_correspondence(request: CorrespondenceConversionRequest) -> CorrespondenceConversionResponse:
    return _converter.build(request)
