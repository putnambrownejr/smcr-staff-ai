from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.career_opportunities import (
    CareerOpportunityListResponse,
    CareerOpportunityRefreshAllResponse,
    CareerOpportunitySortField,
    CareerOpportunitySourceState,
    OpportunityQuery,
    OpportunitySourceKey,
    SortDirection,
)
from app.schemas.opportunities import OpportunityType
from app.services.opportunities.feed_service import CareerOpportunityFeedService
from app.services.opportunities.feed_store import CareerOpportunityFeedStore

router = APIRouter(
    prefix="/career-opportunities",
    tags=["career opportunities"],
    dependencies=[LocalApiKeyDependency],
)


def get_career_opportunity_service() -> Iterator[CareerOpportunityFeedService]:
    settings = get_settings()
    yield CareerOpportunityFeedService(CareerOpportunityFeedStore(settings.career_opportunities_storage_dir))


@router.get("", response_model=CareerOpportunityListResponse)
def list_career_opportunities(
    service: Annotated[CareerOpportunityFeedService, Depends(get_career_opportunity_service)],
    sort_by: CareerOpportunitySortField = CareerOpportunitySortField.source_order,
    direction: SortDirection = SortDirection.ascending,
    opportunity_type: Annotated[list[OpportunityType] | None, Query()] = None,
    rank: str | None = None,
    mos: str | None = None,
    location: str | None = None,
    source: str | None = None,
    keyword: str | None = None,
) -> CareerOpportunityListResponse:
    return service.query(
        OpportunityQuery(
            sort_by=sort_by,
            direction=direction,
            opportunity_types=opportunity_type or [],
            rank=rank,
            mos=mos,
            location=location,
            source=source,
            keyword=keyword,
        )
    )


@router.get("/sources", response_model=list[CareerOpportunitySourceState])
def list_career_opportunity_sources(
    service: Annotated[CareerOpportunityFeedService, Depends(get_career_opportunity_service)],
) -> list[CareerOpportunitySourceState]:
    return service.source_states()


@router.post("/refresh", response_model=CareerOpportunityRefreshAllResponse)
async def refresh_all_career_opportunities(
    service: Annotated[CareerOpportunityFeedService, Depends(get_career_opportunity_service)],
) -> CareerOpportunityRefreshAllResponse:
    return await service.refresh_all()


@router.post("/sources/{source_key}/refresh", response_model=CareerOpportunitySourceState)
async def refresh_career_opportunity_source(
    source_key: OpportunitySourceKey,
    service: Annotated[CareerOpportunityFeedService, Depends(get_career_opportunity_service)],
) -> CareerOpportunitySourceState:
    return await service.refresh(source_key)
