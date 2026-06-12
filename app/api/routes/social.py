from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.social import SocialIngestRequest, SocialIngestResponse, VettedSocialSource
from app.services.ingestion.social_media_connector import SocialMediaVettedConnector

router = APIRouter(prefix="/social", tags=["vetted social sources"], dependencies=[LocalApiKeyDependency])

_connector = SocialMediaVettedConnector()


@router.get("/sources", response_model=list[VettedSocialSource])
def list_vetted_social_sources() -> list[VettedSocialSource]:
    return _connector.vetted_sources()


@router.post("/ingest", response_model=SocialIngestResponse)
def ingest_social_trends(request: SocialIngestRequest) -> SocialIngestResponse:
    return _connector.ingest(request)
