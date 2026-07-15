# Career Opportunities Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate public SMCR, IMA, and ADOS/active-duty opportunities into a refreshable, sortable, filterable Watch widget with truthful caching and official link-outs.

**Architecture:** Replace the obsolete single-page billet fetch with an allowlisted source registry, typed MARFORRES adapters, and a public local cache that preserves the last successful result per source. Add pure query functions for sorting/filtering and reuse deterministic recommendation scoring only for records with sufficient structured data. The Watch UI is generated through the existing dashboard patch script and uses independent source refresh states.

**Tech Stack:** Python 3.12, FastAPI, httpx, BeautifulSoup, Pydantic v2, flat JSON storage, vanilla JS compiled dashboard, pytest, Playwright, mypy, ruff.

## Global Constraints

- UNCLASSIFIED public data only.
- Use only allowlisted official `.mil` or approved DoD source URLs; reject arbitrary client-supplied URLs.
- Never interpret parser failure as “no billets,” invent dates/eligibility/duration, expose test fixtures in personal mode, authenticate to DoD systems, submit forms, or auto-apply.
- Each row links to an official listing or official source.
- Missing fields remain null and display `Not provided` or `Date unavailable`.
- Recommendation controls are optional and appear only when exact match reasons can be explained from structured data.
- No new runtime dependency, browser-automation dependency, background scheduler, database migration, cloud service, or frontend framework.
- Every advisory surface states that availability and eligibility require official verification.

---

## File Structure

- Modify `app/schemas/billets.py`: current source keys and normalized billet fields.
- Modify `app/schemas/opportunities.py`: component types, provenance, detected/last-seen timestamps, optional source order.
- Create `app/schemas/career_opportunities.py`: source metadata, refresh outcome, list/query response models.
- Create `app/services/opportunities/query.py`: pure filter and stable sort behavior.
- Create `app/services/ingestion/marforres_opportunity_adapter.py`: allowlisted source registry, link discovery, HTML/table/card normalization.
- Create `app/services/opportunities/feed_store.py`: per-source cache and refresh metadata.
- Create `app/services/opportunities/feed_service.py`: independent refresh and cached fallback orchestration.
- Create `app/api/routes/career_opportunities.py`: list sources/records and refresh one/all.
- Modify `app/core/config.py` and `app/main.py`: storage path and route registration.
- Modify `app/services/billets/recommender.py` and `app/services/opportunities/tracker.py`: gated scoring and full provenance.
- Modify `scripts/patch_dashboard_bundle.py`; regenerate `app/static/dashboard/index.html`.
- Create representative public-structure fixtures under `tests/fixtures/` and focused tests under `tests/`.
- Modify `tests/test_dashboard.py` and `tests/e2e/test_dashboard_flows.py`.

### Task 1: Normalized records, sorting, and filtering

**Files:**
- Modify: `app/schemas/billets.py`
- Modify: `app/schemas/opportunities.py`
- Create: `app/schemas/career_opportunities.py`
- Create: `app/services/opportunities/query.py`
- Test: `tests/test_opportunity_query.py`

**Interfaces:**
- Produces: `OpportunityType`, `CareerOpportunitySortField`, `SortDirection`, `OpportunityQuery`, `query_opportunities(records, query)`.
- Consumes: existing `OpportunityRecord` fields and Marine grade normalization.

- [ ] **Step 1: Write failing tests for every sort family and composed filters**

```python
from datetime import UTC, date, datetime

from app.schemas.career_opportunities import CareerOpportunitySortField, OpportunityQuery, SortDirection
from app.schemas.opportunities import OpportunityRecord
from app.services.opportunities.query import query_opportunities


def records() -> list[OpportunityRecord]:
    return [
        OpportunityRecord(opportunity_id="ima-major", title="Planner", opportunity_type="ima", rank="Maj",
                          mos="0505", location="Quantico, VA", source_name="Reserve Billets", source_order=2,
                          published_at=date(2026, 7, 1), tracked=False),
        OpportunityRecord(opportunity_id="smcr-capt", title="Communications Officer", opportunity_type="smcr",
                          rank="Capt", mos="0602", location="Austin, TX", source_name="Reserve Billets",
                          source_order=1, published_at=None, tracked=False),
        OpportunityRecord(opportunity_id="ados-ltcol", title="ADOS G-6", opportunity_type="ados", rank="LtCol",
                          mos="0602", location="New Orleans, LA", source_name="Active Billets", source_order=1,
                          published_at=date(2026, 7, 10), tracked=False),
    ]


def test_rank_sort_uses_grade_order() -> None:
    result = query_opportunities(records(), OpportunityQuery(sort_by=CareerOpportunitySortField.rank,
                                                              direction=SortDirection.ascending))
    assert [item.rank for item in result] == ["Capt", "Maj", "LtCol"]


def test_date_sort_keeps_missing_dates_last_in_both_directions() -> None:
    for direction in SortDirection:
        result = query_opportunities(records(), OpportunityQuery(sort_by="published_at", direction=direction))
        assert result[-1].published_at is None


def test_filters_compose_and_clear_to_source_order() -> None:
    result = query_opportunities(records(), OpportunityQuery(opportunity_types=["ima", "ados"], mos="06",
                                                              keyword="g-6"))
    assert [item.opportunity_id for item in result] == ["ados-ltcol"]
    default = query_opportunities(records(), OpportunityQuery())
    assert [item.source_order for item in default if item.source_name == "Reserve Billets"] == [1, 2]
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_opportunity_query.py -q`

Expected: imports fail because the query schema/service does not exist.

- [ ] **Step 3: Extend normalized record types**

```python
class OpportunityType(StrEnum):
    smcr = "smcr"
    ima = "ima"
    ados = "ados"
    ia_jia = "ia_jia"
    other = "other"


class OpportunityRecord(BaseModel):
    opportunity_id: str
    title: str
    opportunity_type: OpportunityType
    unit: str | None = None
    location: str | None = None
    mos: str | None = None
    rank: str | None = None
    rank_min: str | None = None
    rank_max: str | None = None
    duration: str | None = None
    published_at: date | None = None
    due_date: date | None = None
    source_url: str | None = None
    direct_url: str | None = None
    source_name: str | None = None
    description: str | None = None
    notes: str | None = None
    source_order: int | None = None
    match_score: int | None = None
    match_reasons: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tracked: bool = False
    tracked_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
```

Add backward-compatible input normalization so stored `smcr_bic` records validate as `smcr`. Update manual request defaults and conversions accordingly.

- [ ] **Step 4: Add concrete query types and pure stable sorting**

```python
class CareerOpportunitySortField(StrEnum):
    source_order = "source_order"
    title = "title"
    opportunity_type = "opportunity_type"
    rank = "rank"
    mos = "mos"
    unit = "unit"
    location = "location"
    duration = "duration"
    published_at = "published_at"
    due_date = "due_date"
    match_score = "match_score"


class SortDirection(StrEnum):
    ascending = "ascending"
    descending = "descending"


class OpportunityQuery(BaseModel):
    sort_by: CareerOpportunitySortField = CareerOpportunitySortField.source_order
    direction: SortDirection = SortDirection.ascending
    opportunity_types: list[OpportunityType] = Field(default_factory=list)
    rank: str | None = None
    mos: str | None = None
    location: str | None = None
    source: str | None = None
    keyword: str | None = None


class OpportunitySourceKey(StrEnum):
    reserve_billets = "reserve_billets"
    active_billets = "active_billets"


class OpportunitySource(BaseModel):
    key: OpportunitySourceKey
    name: str
    url: str
    default_type: OpportunityType
    description: str = ""


class OpportunityRefreshOutcome(StrEnum):
    listings_refreshed = "listings_refreshed"
    link_only = "link_only"
    failed_cached = "failed_cached"
    failed_no_cache = "failed_no_cache"


class OpportunityParseResult(BaseModel):
    source: OpportunitySource
    records: list[OpportunityRecord] = Field(default_factory=list)
    official_links: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CareerOpportunitySourceState(BaseModel):
    source: OpportunitySource
    outcome: OpportunityRefreshOutcome
    records: list[OpportunityRecord] = Field(default_factory=list)
    official_links: list[str] = Field(default_factory=list)
    refreshed_at: datetime | None = None
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_successful_at: datetime | None = None
    last_error: str | None = None
    warnings: list[str] = Field(default_factory=list)


class CareerOpportunityRefreshAllResponse(BaseModel):
    results: list[CareerOpportunitySourceState] = Field(default_factory=list)


class CareerOpportunityListResponse(BaseModel):
    total_records: int
    records: list[OpportunityRecord] = Field(default_factory=list)
    sources: list[CareerOpportunitySourceState] = Field(default_factory=list)


def query_opportunities(records: Sequence[OpportunityRecord], query: OpportunityQuery) -> list[OpportunityRecord]:
    filtered = [record for record in records if _matches(record, query)]
    present = [record for record in filtered if _raw_sort_value(record, query.sort_by) is not None]
    missing = [record for record in filtered if _raw_sort_value(record, query.sort_by) is None]
    present.sort(key=lambda record: (_normalized_sort_value(record, query.sort_by), record.source_order or 10**9),
                 reverse=query.direction is SortDirection.descending)
    return [*present, *missing]


GRADE_ORDER = {"2NDLT": 1, "O1": 1, "1STLT": 2, "O2": 2, "CAPT": 3, "O3": 3,
               "MAJ": 4, "O4": 4, "LTCOL": 5, "O5": 5, "COL": 6, "O6": 6,
               "LCPL": 103, "E3": 103, "CPL": 104, "E4": 104, "SGT": 105, "E5": 105,
               "SSGT": 106, "E6": 106, "GYSGT": 107, "E7": 107,
               "MSGT": 108, "1STSGT": 108, "E8": 108, "MGYSGT": 109, "SGTMAJ": 109, "E9": 109}


def _matches(record: OpportunityRecord, query: OpportunityQuery) -> bool:
    if query.opportunity_types and record.opportunity_type not in query.opportunity_types:
        return False
    checks = [(query.rank, record.rank), (query.mos, record.mos),
              (query.location, record.location), (query.source, record.source_name)]
    if any(needle and needle.casefold() not in (value or "").casefold() for needle, value in checks):
        return False
    if query.keyword:
        haystack = " ".join(value or "" for value in
                            [record.title, record.unit, record.location, record.mos, record.rank,
                             record.description, record.notes]).casefold()
        if query.keyword.casefold() not in haystack:
            return False
    return True


def _raw_sort_value(record: OpportunityRecord, field: CareerOpportunitySortField) -> object | None:
    return getattr(record, field.value, None)


def _normalized_sort_value(record: OpportunityRecord, field: CareerOpportunitySortField) -> object:
    value = _raw_sort_value(record, field)
    if field is CareerOpportunitySortField.rank:
        normalized = str(value or "").upper().replace("-", "").replace(" ", "")
        return (GRADE_ORDER.get(normalized, 10**6), normalized)
    if field is CareerOpportunitySortField.opportunity_type:
        return record.opportunity_type.value
    if isinstance(value, str):
        return value.casefold()
    return value if value is not None else ""
```

Reuse or extract the existing rank equivalents rather than maintaining two divergent production mappings. Unknown ranks sort after known ranks without changing display text.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/test_opportunity_query.py tests/test_opportunities.py tests/test_billets.py -q`

Expected: all tests pass, including compatibility tests.

```powershell
git add app/schemas/billets.py app/schemas/opportunities.py app/schemas/career_opportunities.py app/services/opportunities/query.py tests/test_opportunity_query.py tests/test_opportunities.py tests/test_billets.py
git commit -m "feat: normalize and query career opportunities"
```

### Task 2: Allowlisted MARFORRES source adapters

**Files:**
- Create: `app/services/ingestion/marforres_opportunity_adapter.py`
- Modify: `app/services/ingestion/smcr_bic_scraper.py`
- Create: `tests/fixtures/marforres_reserve_billets.html`
- Create: `tests/fixtures/marforres_active_billets.html`
- Create: `tests/test_marforres_opportunity_adapter.py`
- Modify: `tests/test_billets.py`

**Interfaces:**
- Produces: `OFFICIAL_OPPORTUNITY_SOURCES`, `MarforresOpportunityAdapter.fetch(source_key)`, `parse(html, source)`.
- Consumes: `OpportunityRecord`, httpx, BeautifulSoup.

- [ ] **Step 1: Add representative fixtures and failing adapter tests**

The reserve fixture must include separate `SMCR Billets` and `IMA Billets` sections, a table with title/unit/location/rank/MOS/duration, and an official active-billets link. The active fixture must include officer/enlisted headings, an ADOS row, and the official `forms.osi.apps.mil` application link.

```python
def test_adapter_parses_smcr_and_ima_sections() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.reserve_billets]
    html = Path("tests/fixtures/marforres_reserve_billets.html").read_text(encoding="utf-8")
    result = MarforresOpportunityAdapter().parse(html, source)
    assert {record.opportunity_type.value for record in result.records} == {"smcr", "ima"}
    assert all(record.source_url == source.url for record in result.records)
    assert result.official_links


def test_adapter_parses_ados_and_preserves_application_link() -> None:
    source = OFFICIAL_OPPORTUNITY_SOURCES[OpportunitySourceKey.active_billets]
    html = Path("tests/fixtures/marforres_active_billets.html").read_text(encoding="utf-8")
    result = MarforresOpportunityAdapter().parse(html, source)
    assert result.records[0].opportunity_type.value == "ados"
    assert result.records[0].direct_url.startswith("https://forms.osi.apps.mil/")


def test_adapter_rejects_non_allowlisted_source() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        MarforresOpportunityAdapter().fetch_url("https://example.test/billets")
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_marforres_opportunity_adapter.py -q`

Expected: import failure for the new adapter.

- [ ] **Step 3: Define the canonical registry and bounded fetch**

```python
OFFICIAL_OPPORTUNITY_SOURCES = {
    OpportunitySourceKey.reserve_billets: OpportunitySource(
        key=OpportunitySourceKey.reserve_billets,
        name="MARFORRES Reserve Billets",
        url="https://www.marforres.marines.mil/About/Reserve-Billets/",
        default_type=OpportunityType.smcr,
    ),
    OpportunitySourceKey.active_billets: OpportunitySource(
        key=OpportunitySourceKey.active_billets,
        name="MARFORRES Active Billets / Find",
        url="https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-1-Administration/Active-Billets/Find/",
        default_type=OpportunityType.ados,
    ),
}
```

Import `OpportunitySourceKey` and `OpportunitySource` from `app.schemas.career_opportunities`.

`fetch` must use `httpx.AsyncClient(timeout=15, follow_redirects=True)`, reject bodies over 5 MiB, accept only HTML for the first implementation, and fetch only URLs obtained from the registry. Discovered links are returned but not recursively fetched unless they pass an explicit host/path allowlist.

- [ ] **Step 4: Implement section-aware table/card parsing and truthful link-only results**

Normalize headers using the existing scraper helpers. Determine component only from the enclosing labeled section or explicit row field; otherwise use `other`. Generate stable fingerprints from source key plus normalized title/unit/location/MOS/rank. If no structured rows exist, return `records=[]`, discovered official links, and warning `Official source loaded, but no structured opportunity rows were available.`

Keep `SmcrBicScraper` as a compatibility wrapper that delegates to the reserve source adapter; change `MARFORRES_BILLETS_URL` to the current gateway.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/test_marforres_opportunity_adapter.py tests/test_billets.py -q`

Expected: all tests pass.

```powershell
git add app/services/ingestion/marforres_opportunity_adapter.py app/services/ingestion/smcr_bic_scraper.py tests/fixtures/marforres_reserve_billets.html tests/fixtures/marforres_active_billets.html tests/test_marforres_opportunity_adapter.py tests/test_billets.py
git commit -m "feat: ingest official MARFORRES opportunities"
```

### Task 3: Cache, refresh orchestration, and API

**Files:**
- Create: `app/services/opportunities/feed_store.py`
- Create: `app/services/opportunities/feed_service.py`
- Create: `app/api/routes/career_opportunities.py`
- Modify: `app/core/config.py`
- Modify: `app/main.py`
- Test: `tests/test_career_opportunity_feed.py`
- Test: `tests/test_career_opportunity_routes.py`

**Interfaces:**
- Consumes: adapter and schemas from Tasks 1–2.
- Produces: `CareerOpportunityFeedStore`, `CareerOpportunityFeedService`, `/career-opportunities` routes.

- [ ] **Step 1: Write failing cache-fallback and partial-success tests**

```python
@pytest.mark.asyncio
async def test_refresh_failure_retains_last_successful_cache(tmp_path: Path) -> None:
    store = CareerOpportunityFeedStore(tmp_path)
    service = CareerOpportunityFeedService(store, adapter=FakeAdapter(success=True))
    first = await service.refresh(OpportunitySourceKey.reserve_billets)
    service.adapter = FakeAdapter(success=False)
    second = await service.refresh(OpportunitySourceKey.reserve_billets)
    assert second.outcome.value == "failed_cached"
    assert second.records == first.records
    assert second.last_successful_at == first.refreshed_at


@pytest.mark.asyncio
async def test_refresh_all_allows_partial_success(tmp_path: Path) -> None:
    service = CareerOpportunityFeedService(CareerOpportunityFeedStore(tmp_path), adapter=MixedFakeAdapter())
    result = await service.refresh_all()
    assert {item.source.key: item.outcome.value for item in result.results} == {
        OpportunitySourceKey.reserve_billets: "listings_refreshed",
        OpportunitySourceKey.active_billets: "failed_no_cache",
    }
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_career_opportunity_feed.py tests/test_career_opportunity_routes.py -q`

Expected: import failures for feed store/service/routes.

- [ ] **Step 3: Implement atomic per-source cache and state records**

```python
class CareerOpportunityFeedStore:
    def save_success(self, source: OpportunitySource, records: list[OpportunityRecord],
                     official_links: list[str], refreshed_at: datetime) -> CareerOpportunitySourceState:
        state = CareerOpportunitySourceState(source=source, outcome="listings_refreshed" if records else "link_only",
                                             records=records, official_links=official_links,
                                             refreshed_at=refreshed_at, last_successful_at=refreshed_at)
        target = self._path(source.key)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(target)
        return state

    def load(self, source_key: OpportunitySourceKey) -> CareerOpportunitySourceState | None:
        path = self._path(source_key)
        return CareerOpportunitySourceState.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None
```

On failure, do not overwrite the cached records. Return a copied state with current `last_checked_at`, `last_error`, and `failed_cached` or `failed_no_cache` outcome.

- [ ] **Step 4: Add service and routes**

Expose:

- `GET /career-opportunities/sources`
- `GET /career-opportunities/records` with typed filter/sort query parameters
- `POST /career-opportunities/sources/{source_key}/refresh`
- `POST /career-opportunities/refresh`

Configure `career_opportunity_feed_storage_dir = default_local_context_dir() / "career_opportunity_feed"`, add it to `configured_storage_dirs`, import/register the route in `app/main.py`, and return HTTP 422 for an unknown enum source key without accepting a URL.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/test_career_opportunity_feed.py tests/test_career_opportunity_routes.py -q`

Expected: all tests pass.

```powershell
git add app/core/config.py app/main.py app/api/routes/career_opportunities.py app/services/opportunities/feed_store.py app/services/opportunities/feed_service.py tests/test_career_opportunity_feed.py tests/test_career_opportunity_routes.py
git commit -m "feat: cache and refresh career opportunities"
```

### Task 4: Explainable profile matching and tracking provenance

**Files:**
- Modify: `app/services/billets/recommender.py`
- Modify: `app/services/opportunities/tracker.py`
- Modify: `app/schemas/opportunities.py`
- Modify: `tests/test_billets.py`
- Modify: `tests/test_opportunities.py`

**Interfaces:**
- Produces: `can_score(record, profile) -> bool`, complete source provenance in tracked records.
- Consumes: normalized live records and existing deterministic scorer.

- [ ] **Step 1: Add failing gating and provenance tests**

```python
def test_unstructured_record_is_visible_but_unscored() -> None:
    record = SmcrBillet(title="Open official opportunities", source_url="https://www.marforres.marines.mil/")
    assert recommend_billets([record], BilletUserProfile(mos="0602", rank="Capt")) == []


def test_tracked_record_keeps_source_and_last_seen(tmp_path: Path) -> None:
    tracker = OpportunityTracker(tmp_path)
    request = ManualOpportunityRequest(title="ADOS G-6", opportunity_type="ados", mos="0602", rank="Capt",
                                       source_name="MARFORRES Active Billets", source_url="https://www.marforres.marines.mil/",
                                       direct_url="https://forms.osi.apps.mil/r/example",
                                       last_seen_at=datetime(2026, 7, 15, tzinfo=UTC))
    record = tracker.track([request])[0]
    assert record.direct_url == request.direct_url
    assert record.last_seen_at == request.last_seen_at


def test_tracking_is_user_scoped(tmp_path: Path) -> None:
    tracker = OpportunityTracker(tmp_path)
    tracker.track([ManualOpportunityRequest(title="IMA Planner", opportunity_type="ima")], user_key="capt-a")
    assert len(tracker.list(user_key="capt-a")) == 1
    assert tracker.list(user_key="capt-b") == []
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_billets.py tests/test_opportunities.py -q`

Expected: at least the provenance fields are rejected or lost.

- [ ] **Step 3: Gate scoring and preserve provenance**

```python
def can_score(billet: SmcrBillet, profile: BilletUserProfile) -> bool:
    return bool((profile.mos and billet.mos) or (profile.rank and any([billet.rank, billet.rank_min, billet.rank_max])))


def recommend_billets(billets: list[SmcrBillet], profile: BilletUserProfile,
                      max_results: int = 10) -> list[BilletRecommendation]:
    recommendations = [_score_billet(billet, profile) for billet in billets if can_score(billet, profile)]
    recommendations.sort(key=lambda item: item.score, reverse=True)
    return [item for item in recommendations if item.score > 0][:max_results]
```

Add `direct_url`, `duration`, `published_at`, `last_seen_at`, and source-order fields to manual requests and copy them through `_record_from_manual`. Keep existing stored records readable through defaults.

Make tracking explicitly user-scoped while preserving existing callers with a local default:

```python
DEFAULT_OPPORTUNITY_USER_KEY = "local-user"

def track(self, opportunities: Sequence[ManualOpportunityRequest],
          user_key: str = DEFAULT_OPPORTUNITY_USER_KEY) -> Sequence[OpportunityRecord]:
    if not is_valid_user_key(user_key):
        raise ValueError("Invalid user_key.")
    tracked = [self._record_from_manual(opportunity) for opportunity in opportunities]
    for record in tracked:
        self._path(record.opportunity_id, user_key).write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return tracked

def list(self, opportunity_type: OpportunityType | None = None,
         user_key: str = DEFAULT_OPPORTUNITY_USER_KEY) -> Sequence[OpportunityRecord]:
    prefix = hashlib.sha256(user_key.encode()).hexdigest()[:24] + "-"
    records = [OpportunityRecord.model_validate_json(path.read_text(encoding="utf-8"))
               for path in sorted(self.root_dir.glob(f"{prefix}*.json"))]
    return [record for record in records if opportunity_type is None or record.opportunity_type == opportunity_type]
```

Update `/opportunities/track` to pass `request.user_key or DEFAULT_OPPORTUNITY_USER_KEY`, and add `user_key` as a query parameter to `GET /opportunities`. Existing unprefixed local records are read only for the default user and may be rewritten with the prefix when next tracked.

- [ ] **Step 4: Run tests and commit**

Run: `uv run pytest tests/test_billets.py tests/test_opportunities.py tests/test_career_watch.py tests/test_chief_orchestrator.py -q`

Expected: all tests pass.

```powershell
git add app/schemas/opportunities.py app/services/billets/recommender.py app/services/opportunities/tracker.py tests/test_billets.py tests/test_opportunities.py
git commit -m "feat: explain opportunity matches and provenance"
```

### Task 5: Watch widget, sort/filter controls, and independent refresh

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Regenerate: `app/static/dashboard/index.html`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`

**Interfaces:**
- Consumes: `/career-opportunities` API from Task 3.
- Produces: Career Opportunities sub-card under Connected Feeds.

- [ ] **Step 1: Add failing dashboard and browser assertions**

```python
def test_dashboard_contains_career_opportunities_widget_and_sort_fields() -> None:
    source = dashboard_html()
    assert "Career opportunities" in source
    assert "/career-opportunities/records" in source
    for label in ["Title", "Component", "Rank", "MOS", "Unit", "Location", "Duration",
                  "Published", "Due date"]:
        assert label in source
    assert "Open official source" in source
    assert "Date unavailable" in source
```

Add a Playwright flow that opens Watch, filters to IMA, sorts by rank ascending then descending, clears filters, sorts by publication date, and verifies missing dates render after dated rows.

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_dashboard.py::test_dashboard_contains_career_opportunities_widget_and_sort_fields -q`

Expected: assertion failure because the widget is absent.

- [ ] **Step 3: Patch dashboard state, API methods, and UI**

Add `careerOpportunitySources`, `careerOpportunities`, `careerOpportunitySort`, `careerOpportunityDirection`, filter values, global status, and per-source status map. Add `_loadCareerOpportunities`, `_refreshCareerOpportunitySource`, `_refreshAllCareerOpportunities`, and computed filtered/sorted rows.

Use this exact source action behavior:

```javascript
async _refreshCareerOpportunitySource(sourceKey) {
  this.setState((s) => ({ careerOpportunityRefresh: { ...s.careerOpportunityRefresh, [sourceKey]: "Refreshing…" } }));
  try {
    const response = await fetch("/career-opportunities/sources/" + encodeURIComponent(sourceKey) + "/refresh",
                                 { method: "POST", headers: this._apiHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Refresh failed.");
    this.setState((s) => ({ careerOpportunityRefresh: { ...s.careerOpportunityRefresh,
      [sourceKey]: data.outcome === "failed_cached" ? "Refresh failed · showing cached" : "Refreshed" } }));
    await this._loadCareerOpportunities();
  } catch (error) {
    this.setState((s) => ({ careerOpportunityRefresh: { ...s.careerOpportunityRefresh,
      [sourceKey]: "Refresh failed · open official source" } }));
  }
}
```

Render each row with supplied fields, `Date unavailable` for null dates, and `Open official listing` when `direct_url` exists or `Open official source` using `source_url`. Default to newest publication date when any record has one; otherwise preserve source order and display that fallback.

- [ ] **Step 4: Regenerate, test, and verify idempotence**

Run: `uv run python scripts/patch_dashboard_bundle.py`

Expected: successful patch.

Run: `uv run pytest tests/test_dashboard.py tests/e2e/test_dashboard_flows.py -q`

Expected: dashboard assertions and browser flow pass.

Run twice: `uv run python scripts/patch_dashboard_bundle.py`

Expected: the second run produces no Git diff.

- [ ] **Step 5: Commit the Watch widget**

```powershell
git add scripts/patch_dashboard_bundle.py app/static/dashboard/index.html tests/test_dashboard.py tests/e2e/test_dashboard_flows.py
git commit -m "feat: add career opportunities watch widget"
```

### Task 6: Live-source check and full validation

**Files:**
- Modify only files implicated by validation failures.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: independently releasable Career Opportunities feature.

- [ ] **Step 1: Perform a bounded live-source smoke check**

Run: `uv run python -c "import asyncio; from pathlib import Path; from app.services.opportunities.feed_store import CareerOpportunityFeedStore; from app.services.opportunities.feed_service import CareerOpportunityFeedService; from app.schemas.career_opportunities import OpportunitySourceKey; result=asyncio.run(CareerOpportunityFeedService(CareerOpportunityFeedStore(Path('.tmp-career-smoke'))).refresh(OpportunitySourceKey.reserve_billets)); print(result.outcome.value, len(result.official_links))"`

Expected: `listings_refreshed`, `link_only`, `failed_cached`, or `failed_no_cache`, followed by an official-link count. Delete only the verified repository-local `.tmp-career-smoke` directory after inspecting the result.

- [ ] **Step 2: Run opportunity and dashboard tests**

Run: `uv run pytest tests/test_opportunity_query.py tests/test_marforres_opportunity_adapter.py tests/test_career_opportunity_feed.py tests/test_career_opportunity_routes.py tests/test_billets.py tests/test_opportunities.py tests/test_dashboard.py tests/e2e/test_dashboard_flows.py -q`

Expected: all tests pass.

- [ ] **Step 3: Run static and full-suite checks**

Run: `uv run mypy app tests`

Expected: no errors.

Run: `uv run ruff check .`

Expected: no errors.

Run: `uv run pytest tests/ -q`

Expected: full suite passes with only the repository's documented skips/deselections.

- [ ] **Step 4: Review cohesion in the running dashboard**

Verify Watch refresh-all, each source refresh, cached failure copy, external links, all sort directions, filters, Demo-off behavior, and the existing Connected Feeds controls. Confirm no sample fixture appears in personal mode.

- [ ] **Step 5: Commit a validation fix only when files changed**

Run: `git status --short`

When validation changed files, stage the named files reported by `git status --short` and commit:

```powershell
git commit -m "fix: harden career opportunity refresh"
```

When the worktree is clean, do not create an empty commit.
