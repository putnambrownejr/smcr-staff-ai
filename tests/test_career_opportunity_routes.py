from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.career_opportunities import get_career_opportunity_service
from app.main import app
from app.schemas.career_opportunities import OpportunityParseResult, OpportunitySourceKey
from app.schemas.opportunities import OpportunityRecord
from app.services.ingestion.marforres_opportunity_adapter import OFFICIAL_OPPORTUNITY_SOURCES
from app.services.opportunities.feed_service import CareerOpportunityFeedService
from app.services.opportunities.feed_store import CareerOpportunityFeedStore


class RouteAdapter:
    async def fetch(self, source_key: OpportunitySourceKey) -> OpportunityParseResult:
        source = OFFICIAL_OPPORTUNITY_SOURCES[source_key]
        opportunity_type = source.default_type
        return OpportunityParseResult(
            source=source,
            records=[
                OpportunityRecord(
                    opportunity_id=f"{source_key.value}-capt",
                    title="Communications Officer"
                    if source_key is OpportunitySourceKey.reserve_billets
                    else "ADOS Planner",
                    opportunity_type=opportunity_type,
                    rank="Capt",
                    mos="0602",
                    source_url=source.url,
                    source_name=source.name,
                    source_order=1,
                )
            ],
            official_links=[source.url],
        )


def test_career_opportunity_routes_refresh_filter_and_sort(tmp_path: Path) -> None:
    service = CareerOpportunityFeedService(CareerOpportunityFeedStore(tmp_path), adapter=RouteAdapter())
    app.dependency_overrides[get_career_opportunity_service] = lambda: service
    client = TestClient(app)
    try:
        refresh = client.post("/career-opportunities/refresh")
        assert refresh.status_code == 200
        assert len(refresh.json()["results"]) == 2

        listing = client.get(
            "/career-opportunities",
            params={"opportunity_type": "smcr", "sort_by": "rank", "direction": "descending"},
        )
        assert listing.status_code == 200
        payload = listing.json()
        assert payload["total_records"] == 1
        assert payload["records"][0]["opportunity_type"] == "smcr"
        assert payload["sources"][0]["source"]["url"].startswith("https://www.marforres.marines.mil/")
    finally:
        app.dependency_overrides.clear()


def test_career_opportunity_route_rejects_unknown_source(tmp_path: Path) -> None:
    service = CareerOpportunityFeedService(CareerOpportunityFeedStore(tmp_path), adapter=RouteAdapter())
    app.dependency_overrides[get_career_opportunity_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post("/career-opportunities/sources/not-allowlisted/refresh")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
