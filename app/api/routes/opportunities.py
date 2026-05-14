from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.opportunities import (
    OpportunityRecommendRequest,
    OpportunityRecommendResponse,
    OpportunityRecord,
    OpportunityTrackRequest,
    OpportunityTrackResponse,
    OpportunityType,
)
from app.services.opportunities.tracker import DEFAULT_OPPORTUNITY_WARNINGS, OpportunityTracker

router = APIRouter(prefix="/opportunities", tags=["career opportunities"], dependencies=[LocalApiKeyDependency])


def get_tracker() -> Iterator[OpportunityTracker]:
    settings = get_settings()
    yield OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities")


@router.get("", response_model=list[OpportunityRecord])
def list_opportunities(
    tracker: Annotated[OpportunityTracker, Depends(get_tracker)],
    opportunity_type: OpportunityType | None = None,
) -> list[OpportunityRecord]:
    return list(tracker.list(opportunity_type=opportunity_type))


@router.post("/track", response_model=OpportunityTrackResponse)
def track_opportunities(
    request: OpportunityTrackRequest,
    tracker: Annotated[OpportunityTracker, Depends(get_tracker)],
) -> OpportunityTrackResponse:
    tracked = tracker.track(request.opportunities)
    return OpportunityTrackResponse(
        tracked=tracked,
        message="Tracked opportunities locally for Chief/Aide and career review workflows.",
    )


@router.post("/recommend", response_model=OpportunityRecommendResponse)
def recommend_opportunities(
    request: OpportunityRecommendRequest,
    tracker: Annotated[OpportunityTracker, Depends(get_tracker)],
) -> OpportunityRecommendResponse:
    return OpportunityRecommendResponse(
        recommendations=tracker.recommend(request.profile, request.opportunities, request.max_results),
        warnings=DEFAULT_OPPORTUNITY_WARNINGS,
    )
