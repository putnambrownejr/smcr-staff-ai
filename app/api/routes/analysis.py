from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResponse
from app.schemas.data_tools import DataMergeRequest, DataMergeResponse
from app.services.analysis.data_merger import DataMergeService
from app.services.analysis.summarizer import TextAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"], dependencies=[LocalApiKeyDependency])
_service = TextAnalysisService()
_merge_service = DataMergeService()


@router.post("/summarize", response_model=TextAnalysisResponse)
def summarize_text(request: TextAnalysisRequest) -> TextAnalysisResponse:
    return _service.analyze(request)


@router.post("/merge-records", response_model=DataMergeResponse)
def merge_records(request: DataMergeRequest) -> DataMergeResponse:
    return _merge_service.analyze(request)
