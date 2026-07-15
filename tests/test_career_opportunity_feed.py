import asyncio
from pathlib import Path

from app.schemas.career_opportunities import (
    OpportunityParseResult,
    OpportunitySourceKey,
)
from app.schemas.opportunities import OpportunityRecord
from app.services.ingestion.marforres_opportunity_adapter import OFFICIAL_OPPORTUNITY_SOURCES
from app.services.opportunities.feed_service import CareerOpportunityFeedService
from app.services.opportunities.feed_store import CareerOpportunityFeedStore


class FakeAdapter:
    def __init__(self, failing: set[OpportunitySourceKey] | None = None) -> None:
        self.failing = failing or set()

    async def fetch(self, source_key: OpportunitySourceKey) -> OpportunityParseResult:
        if source_key in self.failing:
            raise RuntimeError("source unavailable")
        source = OFFICIAL_OPPORTUNITY_SOURCES[source_key]
        return OpportunityParseResult(
            source=source,
            records=[
                OpportunityRecord(
                    opportunity_id=f"{source_key.value}-1",
                    title=f"{source.name} listing",
                    opportunity_type=source.default_type,
                    source_url=source.url,
                    source_name=source.name,
                    source_order=1,
                )
            ],
            official_links=[source.url],
        )


def test_refresh_failure_retains_last_successful_cache(tmp_path: Path) -> None:
    store = CareerOpportunityFeedStore(tmp_path)
    service = CareerOpportunityFeedService(store, adapter=FakeAdapter())
    first = asyncio.run(service.refresh(OpportunitySourceKey.reserve_billets))
    service.adapter = FakeAdapter({OpportunitySourceKey.reserve_billets})

    second = asyncio.run(service.refresh(OpportunitySourceKey.reserve_billets))

    assert second.outcome.value == "failed_cached"
    assert second.records == first.records
    assert second.last_successful_at == first.refreshed_at
    assert second.last_error == "source unavailable"


def test_refresh_all_allows_partial_success(tmp_path: Path) -> None:
    service = CareerOpportunityFeedService(
        CareerOpportunityFeedStore(tmp_path),
        adapter=FakeAdapter({OpportunitySourceKey.active_billets}),
    )

    result = asyncio.run(service.refresh_all())

    assert {item.source.key: item.outcome.value for item in result.results} == {
        OpportunitySourceKey.reserve_billets: "listings_refreshed",
        OpportunitySourceKey.active_billets: "failed_no_cache",
    }


def test_store_round_trips_each_source_independently(tmp_path: Path) -> None:
    store = CareerOpportunityFeedStore(tmp_path)
    service = CareerOpportunityFeedService(store, adapter=FakeAdapter())
    asyncio.run(service.refresh_all())

    assert store.get(OpportunitySourceKey.reserve_billets) is not None
    assert store.get(OpportunitySourceKey.active_billets) is not None
    assert len(store.list()) == 2
