from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.schemas.career_opportunities import (
    CareerOpportunityListResponse,
    CareerOpportunityRefreshAllResponse,
    CareerOpportunitySourceState,
    OpportunityParseResult,
    OpportunityQuery,
    OpportunityRefreshOutcome,
    OpportunitySourceKey,
)
from app.services.ingestion.marforres_opportunity_adapter import (
    OFFICIAL_OPPORTUNITY_SOURCES,
    MarforresOpportunityAdapter,
)
from app.services.opportunities.feed_store import CareerOpportunityFeedStore
from app.services.opportunities.query import query_opportunities


class OpportunityAdapter(Protocol):
    async def fetch(self, source_key: OpportunitySourceKey) -> OpportunityParseResult: ...


class CareerOpportunityFeedService:
    def __init__(
        self,
        store: CareerOpportunityFeedStore,
        adapter: OpportunityAdapter | None = None,
    ) -> None:
        self.store = store
        self.adapter: OpportunityAdapter = adapter or MarforresOpportunityAdapter()

    async def refresh(self, source_key: OpportunitySourceKey) -> CareerOpportunitySourceState:
        checked_at = datetime.now(UTC)
        try:
            parsed = await self.adapter.fetch(source_key)
        except Exception as exc:
            cached = self.store.get(source_key)
            if cached is not None:
                failed = cached.model_copy(
                    update={
                        "outcome": OpportunityRefreshOutcome.failed_cached,
                        "last_checked_at": checked_at,
                        "last_error": str(exc),
                    }
                )
                return self.store.save(failed)
            return CareerOpportunitySourceState(
                source=OFFICIAL_OPPORTUNITY_SOURCES[source_key],
                outcome=OpportunityRefreshOutcome.failed_no_cache,
                last_checked_at=checked_at,
                last_error=str(exc),
                warnings=["Refresh failed. Open the official source and verify current availability."],
            )

        outcome = (
            OpportunityRefreshOutcome.listings_refreshed if parsed.records else OpportunityRefreshOutcome.link_only
        )
        state = CareerOpportunitySourceState(
            source=parsed.source,
            outcome=outcome,
            records=parsed.records,
            official_links=parsed.official_links,
            refreshed_at=checked_at,
            last_checked_at=checked_at,
            last_successful_at=checked_at,
            warnings=parsed.warnings,
        )
        return self.store.save(state)

    async def refresh_all(self) -> CareerOpportunityRefreshAllResponse:
        results = [await self.refresh(source_key) for source_key in OpportunitySourceKey]
        return CareerOpportunityRefreshAllResponse(results=results)

    def query(self, query: OpportunityQuery | None = None) -> CareerOpportunityListResponse:
        states = self.source_states()
        records = [record for state in states for record in state.records]
        queried = query_opportunities(records, query or OpportunityQuery())
        return CareerOpportunityListResponse(
            total_records=len(queried),
            records=queried,
            sources=states,
        )

    def source_states(self) -> list[CareerOpportunitySourceState]:
        cached = {state.source.key: state for state in self.store.list()}
        return [cached.get(key) or _not_refreshed_state(key) for key in OpportunitySourceKey]


def _not_refreshed_state(source_key: OpportunitySourceKey) -> CareerOpportunitySourceState:
    return CareerOpportunitySourceState(
        source=OFFICIAL_OPPORTUNITY_SOURCES[source_key],
        outcome=OpportunityRefreshOutcome.link_only,
        warnings=["Not refreshed yet. Open the official source to verify current availability."],
    )
