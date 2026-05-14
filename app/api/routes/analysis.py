from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResponse
from app.services.analysis.summarizer import TextAnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"], dependencies=[LocalApiKeyDependency])
_service = TextAnalysisService()


@router.post("/summarize", response_model=TextAnalysisResponse)
def summarize_text(request: TextAnalysisRequest) -> TextAnalysisResponse:
    return _service.analyze(request)
