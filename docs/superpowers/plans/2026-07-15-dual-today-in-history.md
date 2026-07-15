# Dual Today in History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show one correctly labeled Marine Corps history entry and one broader U.S. military history entry on Overview, preferring exact-date events and otherwise using the closest cited event.

**Architecture:** Add an explicit history scope and a reusable circular-date selector in the history domain. Load Marine Corps and U.S. military seed catalogs into the same service, expose two typed selections through the existing dashboard workspace response, and adapt the compiled-dashboard patch source to render both selections without inventing dates.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, PyYAML, vanilla JavaScript in the decoded dashboard bundle, pytest, mypy, Ruff.

## Global Constraints

- Runtime remains local-first; do not add a network call during dashboard loading.
- History facts must retain explicit source references, verified against official sources as of 2026-07-15.
- A fallback must display the event's actual date and a `Closest` label; it must not be presented as happening today.
- Unknown or ambiguous event scope must not enter either daily selection.
- Preserve legacy local Marine-history files that predate the scope field by treating them as `usmc` on read.
- Keep the existing history library available.
- Do not stage or modify unrelated pre-existing working-tree changes.
- Every advisory/history presentation remains subject to: `DRAFT — Verify all references against current official sources before acting.`

## File Map

- Modify `app/schemas/history.py`: define scope and selection contracts and add import scope.
- Modify `app/services/history/today_in_history.py`: implement exact/nearest selection and scope-aware markdown extraction.
- Modify `app/services/history/local_history_store.py`: serialize scope enums safely during YAML round trips.
- Create `app/services/history/catalog.py`: own the canonical bundled history seed paths.
- Modify `data/seed/usmc_history_on_this_day.example.yaml`: explicitly mark every existing record `usmc`.
- Create `data/seed/us_military_history_on_this_day.example.yaml`: provide the cited non-USMC U.S. military seed catalog.
- Modify `app/api/routes/history.py`: load both official seed files, carry import scope, and stop ambiguous Wikipedia results from entering selections.
- Modify `app/api/routes/dashboard.py`: load both catalogs and build the two selections once per request.
- Modify `app/schemas/dashboard.py`: expose typed `usmc_history` and `us_military_history` fields.
- Modify `scripts/patch_dashboard_bundle.py`: map and render both response selections in the compiled dashboard.
- Regenerate `app/static/dashboard/index.html`: apply the checked patch source.
- Modify `tests/test_history_import.py`: cover scope, selection, seed validity, import behavior, and year-boundary cases.
- Modify `tests/test_dashboard.py`: cover API parity and decoded-bundle wiring.

---

### Task 1: Typed History Scope and Circular-Date Selector

**Files:**
- Modify: `app/schemas/history.py`
- Modify: `app/services/history/today_in_history.py`
- Modify: `app/services/history/local_history_store.py`
- Test: `tests/test_history_import.py`

**Interfaces:**
- Produces: `HistoryScope`, `HistorySelection`, `TodayInMarineHistoryService.select_for_date(target_date, scope)`, and `extract_history_items_from_markdown(markdown, source_label, scope)`.
- Consumes: existing `TodayInMarineHistoryItem` records and Python `datetime.date`.

- [ ] **Step 1: Write failing selector and compatibility tests**

Add imports and a focused item factory to `tests/test_history_import.py`:

```python
import yaml

from app.schemas.history import HistoryScope, TodayInMarineHistoryItem
from app.services.history.local_history_store import LocalHistoryStore


def _history_item(
    slug: str,
    month: int,
    day: int,
    scope: HistoryScope,
    *,
    year_label: str = "2000",
) -> TodayInMarineHistoryItem:
    return TodayInMarineHistoryItem(
        slug=slug,
        title=slug.replace("-", " ").title(),
        month=month,
        day=day,
        year_label=year_label,
        summary=f"Summary for {slug}.",
        scope=scope,
        references=["https://example.mil/history"],
    )
```

Add these tests:

```python
def test_history_selector_prefers_exact_event_within_scope() -> None:
    service = TodayInMarineHistoryService([
        _history_item("near-usmc", 7, 14, HistoryScope.usmc),
        _history_item("exact-usmc", 7, 15, HistoryScope.usmc),
        _history_item("exact-military", 7, 15, HistoryScope.us_military),
    ])

    marine = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)
    military = service.select_for_date(date(2026, 7, 15), HistoryScope.us_military)

    assert marine is not None and marine.item.slug == "exact-usmc"
    assert marine.is_exact is True and marine.distance_days == 0
    assert military is not None and military.item.slug == "exact-military"


def test_history_selector_uses_previous_event_for_equal_distance_tie() -> None:
    service = TodayInMarineHistoryService([
        _history_item("previous", 7, 14, HistoryScope.usmc),
        _history_item("following", 7, 16, HistoryScope.usmc),
    ])

    selected = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)

    assert selected is not None and selected.item.slug == "previous"
    assert selected.is_exact is False and selected.distance_days == 1


def test_history_selector_wraps_across_year_boundary() -> None:
    service = TodayInMarineHistoryService([
        _history_item("new-years-day", 1, 1, HistoryScope.us_military),
        _history_item("farther", 12, 20, HistoryScope.us_military),
    ])

    selected = service.select_for_date(date(2026, 12, 31), HistoryScope.us_military)

    assert selected is not None and selected.item.slug == "new-years-day"
    assert selected.distance_days == 1


def test_history_selector_returns_none_for_empty_scope() -> None:
    service = TodayInMarineHistoryService([
        _history_item("marine-only", 7, 15, HistoryScope.usmc),
    ])

    assert service.select_for_date(date(2026, 7, 15), HistoryScope.us_military) is None


def test_history_selector_returns_none_when_both_scopes_are_empty() -> None:
    service = TodayInMarineHistoryService([])

    assert service.select_for_date(date(2026, 7, 15), HistoryScope.usmc) is None
    assert service.select_for_date(date(2026, 7, 15), HistoryScope.us_military) is None


def test_history_selector_breaks_same_date_ties_by_year_then_slug() -> None:
    service = TodayInMarineHistoryService([
        _history_item("zulu", 7, 15, HistoryScope.usmc, year_label="1918"),
        _history_item("alpha", 7, 15, HistoryScope.usmc, year_label="1918"),
        _history_item("older", 7, 15, HistoryScope.usmc, year_label="1775"),
    ])

    selected = service.select_for_date(date(2026, 7, 15), HistoryScope.usmc)

    assert selected is not None and selected.item.slug == "older"


def test_legacy_history_record_defaults_to_usmc_scope() -> None:
    item = TodayInMarineHistoryItem.model_validate({
        "slug": "legacy",
        "title": "Legacy Marine event",
        "month": 1,
        "day": 1,
        "year_label": "1900",
        "summary": "Stored before scope metadata existed.",
        "references": ["local-history"],
    })

    assert item.scope is HistoryScope.usmc


def test_history_store_round_trips_scope_as_yaml_string(tmp_path: Path) -> None:
    store = LocalHistoryStore(tmp_path / "history")

    store.replace([_history_item("army", 6, 14, HistoryScope.us_military)])

    raw = yaml.safe_load(store.path.read_text(encoding="utf-8"))
    assert raw["items"][0]["scope"] == "us_military"
    assert store.list_items()[0].scope is HistoryScope.us_military


def test_history_service_skips_malformed_local_catalog(tmp_path: Path) -> None:
    valid_path = tmp_path / "valid.yaml"
    invalid_path = tmp_path / "invalid.yaml"
    valid_path.write_text(
        yaml.safe_dump({"items": [_history_item("valid", 1, 1, HistoryScope.usmc).model_dump(mode="json")]}),
        encoding="utf-8",
    )
    invalid_path.write_text("items: [not: valid: yaml", encoding="utf-8")

    service = TodayInMarineHistoryService.from_paths([valid_path, invalid_path])

    assert [item.slug for item in service.list_items()] == ["valid"]
```

- [ ] **Step 2: Run the new tests and verify the contract is absent**

Run:

```powershell
uv run pytest tests/test_history_import.py -q
```

Expected: collection/import failure because `HistoryScope` and `select_for_date` do not exist yet.

- [ ] **Step 3: Add the schema contracts**

Update `app/schemas/history.py`:

```python
from datetime import date
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class HistoryScope(StrEnum):
    usmc = "usmc"
    us_military = "us_military"


class TodayInMarineHistoryItem(BaseModel):
    slug: str
    title: str
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    year_label: str
    summary: str
    scope: HistoryScope = HistoryScope.usmc
    significance: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_calendar_date(self) -> Self:
        date(2000, self.month, self.day)
        return self


class HistorySelection(BaseModel):
    item: TodayInMarineHistoryItem
    is_exact: bool
    distance_days: int
```

Add the import scope to the existing request model:

```python
class HistoryImportRequest(BaseModel):
    markdown_paths: list[str] = Field(default_factory=list)
    replace_existing: bool = False
    scope: HistoryScope = HistoryScope.usmc
```

- [ ] **Step 4: Implement the deterministic selector**

Update imports and add the selector to `app/services/history/today_in_history.py`:

```python
from app.schemas.history import HistoryScope, HistorySelection, TodayInMarineHistoryItem

_REFERENCE_YEAR = 2000
_DAYS_IN_REFERENCE_YEAR = 366


def _calendar_index(month: int, day: int) -> int:
    return date(_REFERENCE_YEAR, month, day).timetuple().tm_yday - 1
```

Inside `TodayInMarineHistoryService`, replace `get_or_random` with:

```python
    def select_for_date(
        self,
        target_date: date,
        scope: HistoryScope,
    ) -> HistorySelection | None:
        candidates = [item for item in self.items if item.scope is scope]
        if not candidates:
            return None
        target_index = _calendar_index(target_date.month, target_date.day)

        def selection_key(item: TodayInMarineHistoryItem) -> tuple[int, bool, str, str]:
            item_index = _calendar_index(item.month, item.day)
            backward = (target_index - item_index) % _DAYS_IN_REFERENCE_YEAR
            forward = (item_index - target_index) % _DAYS_IN_REFERENCE_YEAR
            distance = min(backward, forward)
            is_following = forward < backward
            return distance, is_following, item.year_label, item.slug

        selected = min(candidates, key=selection_key)
        distance_days = selection_key(selected)[0]
        return HistorySelection(
            item=selected,
            is_exact=distance_days == 0,
            distance_days=distance_days,
        )
```

Keep `get_for_date` for the history library/import tests. Keep `get_or_random` temporarily so this intermediate commit does not break the dashboard; Task 3 removes it immediately after migrating both callers.

Make `from_paths` tolerate one malformed catalog while still loading valid files. Import `ValidationError` from Pydantic and wrap each file/item independently:

```python
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            try:
                with open(path, encoding="utf-8") as handle:
                    payload = yaml.safe_load(handle) or {}
            except (OSError, yaml.YAMLError):
                continue
            if not isinstance(payload, dict):
                continue
            for item_payload in payload.get("items", []):
                try:
                    item = TodayInMarineHistoryItem.model_validate(item_payload)
                except ValidationError:
                    continue
                if item.slug in seen:
                    continue
                seen.add(item.slug)
                items.append(item)
```

- [ ] **Step 5: Serialize history scope values safely**

In `app/services/history/local_history_store.py`, change `_write` to use Pydantic's JSON mode so PyYAML receives plain strings instead of `StrEnum` objects:

```python
    def _write(self, items: list[TodayInMarineHistoryItem]) -> None:
        payload = {"items": [item.model_dump(mode="json") for item in items]}
        with open(self.path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=False)
```

- [ ] **Step 6: Make markdown extraction scope-aware**

Change the function signature and constructed item in `app/services/history/today_in_history.py`:

```python
def extract_history_items_from_markdown(
    markdown: str,
    source_label: str,
    scope: HistoryScope = HistoryScope.usmc,
) -> list[TodayInMarineHistoryItem]:
```

```python
            TodayInMarineHistoryItem(
                slug=slug,
                title=title,
                month=month,
                day=day,
                year_label=year,
                summary=summary,
                scope=scope,
                significance=[],
                references=[source_label],
            )
```

- [ ] **Step 7: Run the selector tests**

Run:

```powershell
uv run pytest tests/test_history_import.py -q
```

Expected: all existing and new history tests pass.

- [ ] **Step 8: Commit the domain change only**

```powershell
git add app/schemas/history.py app/services/history/today_in_history.py app/services/history/local_history_store.py tests/test_history_import.py
git commit -m "feat: add scoped history selection"
```

---

### Task 2: Official U.S. Military Catalog and Safe Imports

**Files:**
- Create: `app/services/history/catalog.py`
- Modify: `data/seed/usmc_history_on_this_day.example.yaml`
- Create: `data/seed/us_military_history_on_this_day.example.yaml`
- Modify: `app/api/routes/history.py`
- Test: `tests/test_history_import.py`

**Interfaces:**
- Consumes: `HistoryScope`, `TodayInMarineHistoryItem`, and scope-aware markdown extraction from Task 1.
- Produces: `BUNDLED_HISTORY_PATHS` and two validated bundled catalogs used by the routes in Task 3.

- [ ] **Step 1: Write failing catalog and import-scope tests**

Add to `tests/test_history_import.py`:

```python
from app.services.history.catalog import BUNDLED_HISTORY_PATHS


def test_bundled_history_catalogs_have_scopes_and_sources() -> None:
    seen_scopes: set[HistoryScope] = set()
    for path in BUNDLED_HISTORY_PATHS:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        assert payload.get("items"), f"No history items in {path}"
        for raw_item in payload["items"]:
            assert "scope" in raw_item, f"Missing explicit scope for {raw_item.get('slug')}"
            item = TodayInMarineHistoryItem.model_validate(raw_item)
            assert item.references, f"Missing source for {item.slug}"
            assert all(reference.startswith("https://") for reference in item.references)
            seen_scopes.add(item.scope)
    assert seen_scopes == {HistoryScope.usmc, HistoryScope.us_military}


def test_markdown_import_preserves_requested_scope() -> None:
    markdown = "- **July 15, 1918 – Rock of the Marne:** The 38th Infantry held its position."

    items = extract_history_items_from_markdown(
        markdown,
        "https://history.army.mil/",
        HistoryScope.us_military,
    )

    assert len(items) == 1
    assert items[0].scope is HistoryScope.us_military
```

Extend the existing route test request with `"scope": "us_military"` and assert the reloaded record has that scope.

- [ ] **Step 2: Run the tests and verify the catalog is absent**

Run:

```powershell
uv run pytest tests/test_history_import.py -q
```

Expected: collection failure for missing `app.services.history.catalog`.

- [ ] **Step 3: Define the canonical seed paths**

Create `app/services/history/catalog.py`:

```python
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SEED_DIR = _REPO_ROOT / "data" / "seed"

BUNDLED_HISTORY_PATHS = (
    _SEED_DIR / "usmc_history_on_this_day.example.yaml",
    _SEED_DIR / "us_military_history_on_this_day.example.yaml",
)
```

- [ ] **Step 4: Add explicit USMC scope to every existing seed record**

In `data/seed/usmc_history_on_this_day.example.yaml`, add this field to all 30 items directly after each slug:

```yaml
    scope: "usmc"
```

Do not change titles, summaries, dates, slugs, significance, or references in this mechanical pass.

- [ ] **Step 5: Create the cited U.S. military seed catalog**

Create `data/seed/us_military_history_on_this_day.example.yaml` with exactly these initial records:

```yaml
items:
  - slug: "us-army-established"
    scope: "us_military"
    title: "Continental Army established"
    month: 6
    day: 14
    year_label: "1775"
    summary: "The Continental Congress authorized the enlistment of expert riflemen, marking the founding date recognized by the United States Army."
    significance:
      - "Provides a joint-service heritage reference for the establishment of the Army."
    references:
      - "https://history.army.mil/Research/Reference-Topics/Army-Birthdays/Branch-Birthday/"
  - slug: "rock-of-the-marne"
    scope: "us_military"
    title: "38th Infantry earns the name Rock of the Marne"
    month: 7
    day: 15
    year_label: "1918"
    summary: "The 38th Infantry Regiment of the 3d Infantry Division held along the Marne against repeated German attacks during the final German offensive of World War I."
    significance:
      - "Highlights disciplined defense and combined infantry-artillery action under severe pressure."
    references:
      - "https://history.army.mil/Portals/143/Images/Publications/Publication%20By%20Title%20Images/A%20Titles%20PDF/CMH_Pub_30-22.pdf?ver=AZSZhsSpAI4Yo0ejWufwlw%3D%3D"
  - slug: "us-coast-guard-founded"
    scope: "us_military"
    title: "Revenue Cutter Service authorized"
    month: 8
    day: 4
    year_label: "1790"
    summary: "President George Washington signed legislation authorizing ten cutters, the founding date officially recognized by the United States Coast Guard."
    significance:
      - "Connects military service with maritime safety, security, and federal law enforcement."
    references:
      - "https://www.history.uscg.mil/home/history-program/"
  - slug: "us-air-force-established"
    scope: "us_military"
    title: "United States Air Force becomes an independent service"
    month: 9
    day: 18
    year_label: "1947"
    summary: "Following the National Security Act of 1947, W. Stuart Symington became Secretary of the Air Force as the new department and independent service took form."
    significance:
      - "Marks the institutional establishment of an independent United States Air Force."
    references:
      - "https://www.af.mil/About-Us/Fact-Sheets/Display/Article/433914/the-birth-of-the-united-states-air-force/"
  - slug: "us-navy-birthday"
    scope: "us_military"
    title: "Continental Navy established"
    month: 10
    day: 13
    year_label: "1775"
    summary: "The Continental Congress authorized the fitting out of armed vessels, a date celebrated as the birthday of the United States Navy."
    significance:
      - "Provides the naval-service heritage context for the Navy's origin."
    references:
      - "https://www.history.navy.mil/today-in-history/october-13.html"
  - slug: "us-space-force-established"
    scope: "us_military"
    title: "United States Space Force established"
    month: 12
    day: 20
    year_label: "2019"
    summary: "The National Defense Authorization Act for Fiscal Year 2020 established the United States Space Force as the sixth branch of the armed forces."
    significance:
      - "Marks the first new United States armed-service branch established in 73 years."
    references:
      - "https://www.spaceforce.mil/News/Article-Display/Article/2045991/department-of-defense-establishes-us-space-force/"
```

- [ ] **Step 6: Load both bundled files in the seed endpoint and preserve import scope**

In `app/api/routes/history.py`, import `BUNDLED_HISTORY_PATHS` and `HistoryScope`, remove `_SEED_PATH`, and implement:

```python
def _load_bundled_history() -> tuple[list[TodayInMarineHistoryItem], list[str]]:
    items: list[TodayInMarineHistoryItem] = []
    warnings: list[str] = []
    for path in BUNDLED_HISTORY_PATHS:
        if not path.exists():
            warnings.append(f"Seed file not found: {path}")
            continue
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        items.extend(
            TodayInMarineHistoryItem.model_validate(item)
            for item in payload.get("items", [])
        )
    return items, warnings
```

Use it in `seed_history_from_bundled_yaml`, returning zero counts only when both files are unavailable. In `import_history_markdown`, pass the request scope:

```python
        extracted = extract_history_items_from_markdown(
            markdown,
            str(path),
            request.scope,
        )
```

- [ ] **Step 7: Prevent ambiguous Wikipedia imports**

Keep `POST /history/refresh` for API compatibility, but stop it from classifying keyword-matched Wikipedia events as U.S. history. Replace its dependency and body with a local-only response:

```python
@router.post("/refresh", response_model=HistoryRefreshResponse)
def refresh_history_for_today(
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
) -> HistoryRefreshResponse:
    return HistoryRefreshResponse(
        fetched_count=0,
        imported_count=0,
        total_available=len(store.list_items()),
        date_checked=datetime.now(UTC).date().isoformat(),
        warnings=[
            "Automated Wikipedia history import is disabled because its events "
            "cannot be assigned a reliable U.S. service scope. Use cited bundled "
            "or explicitly scoped imported records."
        ],
    )
```

Remove `get_wikipedia_service` and the unused Wikipedia import from this route module. Leave the service file in place to avoid an unrelated deletion; it is no longer a dashboard data source.

- [ ] **Step 8: Run catalog and route tests**

Run:

```powershell
uv run pytest tests/test_history_import.py -q
```

Expected: all history tests pass, including explicit scope/source validation.

- [ ] **Step 9: Commit catalog and safe import behavior**

```powershell
git add app/services/history/catalog.py data/seed/usmc_history_on_this_day.example.yaml data/seed/us_military_history_on_this_day.example.yaml app/api/routes/history.py tests/test_history_import.py
git commit -m "feat: add official US military history catalog"
```

---

### Task 3: Dual Dashboard API Contract

**Files:**
- Modify: `app/schemas/dashboard.py`
- Modify: `app/api/routes/dashboard.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `HistorySelection`, `HistoryScope`, `BUNDLED_HISTORY_PATHS`, and `select_for_date`.
- Produces: nullable `usmc_history` and `us_military_history` fields on `DashboardWorkspaceResponse` for Task 4.

- [ ] **Step 1: Write failing demo and personal response assertions**

In `tests/test_dashboard.py`, import `HistoryScope` and add to the demo route test:

```python
    assert payload["usmc_history"]["item"]["scope"] == HistoryScope.usmc
    assert payload["us_military_history"]["item"]["scope"] == HistoryScope.us_military
    assert isinstance(payload["usmc_history"]["is_exact"], bool)
    assert isinstance(payload["us_military_history"]["distance_days"], int)
```

Add the same four assertions to the personal dashboard test. Preserve existing `history_library` assertions.

- [ ] **Step 2: Run targeted API tests and verify fields are absent**

Run:

```powershell
uv run pytest tests/test_dashboard.py::test_demo_dashboard_data_route_returns_workspace_payload tests/test_dashboard.py::test_personal_dashboard_data_route_returns_consolidated_payload -q
```

Expected: failures with missing `usmc_history` / `us_military_history` keys.

- [ ] **Step 3: Extend the dashboard response schema**

In `app/schemas/dashboard.py`, import `HistorySelection` and add:

```python
    usmc_history: HistorySelection | None = None
    us_military_history: HistorySelection | None = None
```

Keep `today_in_history`, `history_is_today`, and `history_library` for compatibility in this change.

- [ ] **Step 4: Load both bundled catalogs**

In `app/api/routes/dashboard.py`, import `HistoryScope`, `HistorySelection`, and `BUNDLED_HISTORY_PATHS`. Change `get_history_service` to:

```python
def get_history_service() -> TodayInMarineHistoryService:
    settings = get_settings()
    local_history_path = Path(settings.history_storage_dir) / "today_in_history.yaml"
    return TodayInMarineHistoryService.from_paths(
        [*BUNDLED_HISTORY_PATHS, local_history_path]
    )
```

- [ ] **Step 5: Build the selections once in each route**

In both personal and demo routes, replace the old `get_or_random`/`get_for_date` arguments with:

```python
    usmc_history = history_service.select_for_date(history_date, HistoryScope.usmc)
    us_military_history = history_service.select_for_date(
        history_date,
        HistoryScope.us_military,
    )
```

Pass both values to `_workspace_response`:

```python
        usmc_history=usmc_history,
        us_military_history=us_military_history,
```

- [ ] **Step 6: Centralize compatibility fields in `_workspace_response`**

Replace its old history arguments with:

```python
    usmc_history: HistorySelection | None,
    us_military_history: HistorySelection | None,
    history_library: list[TodayInMarineHistoryItem],
```

Populate the response as follows:

```python
        usmc_history=usmc_history,
        us_military_history=us_military_history,
        today_in_history=[usmc_history.item] if usmc_history else [],
        history_is_today=bool(usmc_history and usmc_history.is_exact),
        history_library=history_library,
```

This keeps the old Marine-history semantics while the Overview UI moves to the explicit fields.

After both route callers use `select_for_date`, delete `TodayInMarineHistoryService.get_or_random`. Confirm there are no remaining callers:

```powershell
rg -n "get_or_random" app tests
```

Expected: no matches.

- [ ] **Step 7: Run dashboard API and history tests**

Run:

```powershell
uv run pytest tests/test_history_import.py tests/test_dashboard.py::test_demo_dashboard_data_route_returns_workspace_payload tests/test_dashboard.py::test_personal_dashboard_data_route_returns_consolidated_payload -q
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit the API contract**

```powershell
git add app/schemas/dashboard.py app/api/routes/dashboard.py tests/test_dashboard.py
git commit -m "feat: expose dual history selections"
```

---

### Task 4: Render Both History Entries on Overview

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Regenerate: `app/static/dashboard/index.html`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: JSON `usmc_history` and `us_military_history` selections from Task 3.
- Produces: `historyEntries`, `historyVisible`, and `historyMissingLabel` dashboard bindings.

- [ ] **Step 1: Replace the old decoded-bundle assertions with failing dual-entry assertions**

Update `test_dashboard_bundle_renders_history_from_workspace_data`:

```python
def test_dashboard_bundle_renders_dual_history_from_workspace_data() -> None:
    component_source = _decoded_dashboard_component_source()

    assert "data.usmc_history" in component_source
    assert "data.us_military_history" in component_source
    assert "historyEntries" in component_source
    assert '"Marine Corps — Today"' in component_source
    assert '"Closest Marine Corps event"' in component_source
    assert '"U.S. Military — Today"' in component_source
    assert '"Closest U.S. military event"' in component_source
    assert '{{ entry.headline }}' in component_source
    assert '{{ entry.details }}' in component_source
    assert "DRAFT — Verify all references against current official sources before acting." in component_source
    assert "11 JUL 1798 — The U.S. Marine Corps was re-established" not in component_source
```

- [ ] **Step 2: Run the bundle test and verify it fails**

Run:

```powershell
uv run pytest tests/test_dashboard.py::test_dashboard_bundle_renders_dual_history_from_workspace_data -q
```

Expected: failure because the decoded bundle still reads `data.today_in_history` and renders one spotlight.

- [ ] **Step 3: Write a failing patcher-alternative test**

Add to `tests/test_dashboard.py`:

```python
def test_dashboard_patcher_accepts_fresh_or_legacy_source_text() -> None:
    helpers = run_path(str(Path("scripts/patch_dashboard_bundle.py").resolve()))
    apply_patches = helpers["apply_patches"]
    patches = [
        (
            "dual source migration",
            "const dualHistory = true;",
            ("const freshExport = true;", "const legacyHistory = true;"),
            "const dualHistory = true;",
        )
    ]

    assert apply_patches("const freshExport = true;", patches) == "const dualHistory = true;"
    assert apply_patches("const legacyHistory = true;", patches) == "const dualHistory = true;"
    assert apply_patches("const dualHistory = true;", patches) == "const dualHistory = true;"
```

Run:

```powershell
uv run pytest tests/test_dashboard.py::test_dashboard_patcher_accepts_fresh_or_legacy_source_text -q
```

Expected: failure because `apply_patches` currently assumes `old` is one string.

- [ ] **Step 4: Teach the patcher to accept exact alternative old texts**

In `scripts/patch_dashboard_bundle.py`, replace the single-old-text counting block inside `apply_patches` with:

```python
        old_options = (old,) if isinstance(old, str) else old
        matches = [
            (candidate, inner_html.count(candidate))
            for candidate in old_options
            if inner_html.count(candidate)
        ]
        total_matches = sum(count for _, count in matches)
        if total_matches == 0:
            raise SystemExit(
                f"Patch {label!r} target text not found -- the bundle was likely "
                "re-exported and this patch needs updating. Aborting without writing."
            )
        if total_matches > 1:
            raise SystemExit(
                f"Patch {label!r} alternatives matched {total_matches} times "
                "(expected exactly 1). Aborting without writing."
            )
        matched_old = matches[0][0]
        inner_html = inner_html.replace(matched_old, new, 1)
```

Document in the function comment that a tuple of exact `old` alternatives is reserved for migrations that must work against both a fresh design export and an already-patched legacy bundle. Run the new patcher test and expect PASS.

- [ ] **Step 5: Rewrite the existing history workspace/state patches with alternatives**

Do not append a patch that removes the existing markers; rewrite the existing `workspace load` and `workspace store` patch entries so their marker is the final dual-history code and their `old` value is a tuple containing:

1. the exact fresh-export anchor currently stored as that patch's original `old`; and
2. the exact current decoded single-history block currently stored as that patch's `new`.

Both alternatives must produce the same final code. The workspace mapping is:

```javascript
      const usmcHistorySelection = data.usmc_history || null;
      const usMilitaryHistorySelection = data.us_military_history || null;
```

```javascript
        usmcHistorySelection,
        usMilitaryHistorySelection,
```

Use stable markers that appear only in the final code:

```javascript
const usmcHistorySelection = data.usmc_history || null;
usMilitaryHistorySelection,
```

- [ ] **Step 6: Rewrite the presentation mapping/binding patches with alternatives**

Use the same two-alternative pattern for the existing history formatting and binding patch entries: their first old alternative is the fresh-export anchor; their second is the current single-history output. Both produce this local mapper:

```javascript
    const historyMonths = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const mapHistorySelection = (selection, exactLabel, fallbackLabel) => {
      if (!selection || !selection.item) return null;
      const item = selection.item;
      const reference = item.references && item.references[0] || "";
      const sourceIsLink = /^https?:\/\//i.test(reference);
      return {
        label: selection.is_exact ? exactLabel : fallbackLabel,
        headline: String(item.day).padStart(2, "0") + " " + (historyMonths[item.month - 1] || "") + " " + item.year_label + " — " + item.title,
        details: item.summary || "",
        sourceIsLink,
        sourceIsText: !!reference && !sourceIsLink,
        sourceUrl: sourceIsLink ? reference : "",
        sourceLabel: sourceIsLink ? "View source ↗" : reference,
      };
    };
    const usmcHistoryEntry = mapHistorySelection(
      this.state.usmcHistorySelection,
      "Marine Corps — Today",
      "Closest Marine Corps event"
    );
    const usMilitaryHistoryEntry = mapHistorySelection(
      this.state.usMilitaryHistorySelection,
      "U.S. Military — Today",
      "Closest U.S. military event"
    );
    const historyEntries = [usmcHistoryEntry, usMilitaryHistoryEntry].filter(Boolean);
    const historyMissingLabel = !usmcHistoryEntry && usMilitaryHistoryEntry
      ? "Marine Corps history unavailable."
      : (usmcHistoryEntry && !usMilitaryHistoryEntry ? "U.S. military history unavailable." : "");
```

Expose these bindings in the return object:

```javascript
      historyVisible: historyEntries.length > 0,
      historyEntries,
      historyHasMissingScope: !!historyMissingLabel,
      historyMissingLabel,
```

Remove the obsolete `historyLabel`, `historyHeadline`, `historyDetails`, and single-source bindings.

- [ ] **Step 7: Rewrite the history template patch with alternatives**

Rewrite the existing history template patch so its alternatives are the original hardcoded design card and the current single-entry dynamic card. Both produce one expandable `<details>` card with this body:

```html
      <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;">
        <summary style="cursor:pointer;list-style:none;padding:16px 18px;display:flex;gap:14px;align-items:center;">
          <span style="flex:0 0 auto;font-size:0.7rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8a94a0;padding:4px 8px;border:1px solid #313844;border-radius:4px;">Today in history</span>
          <p style="margin:0;font-size:0.88rem;color:#c7cfd8;line-height:1.5;flex:1;">Marine Corps and U.S. military heritage</p>
          <span style="color:#5a6572;font-size:0.8rem;">Details ▾</span>
        </summary>
        <div style="padding:12px 18px 16px;display:grid;gap:12px;border-top:1px solid #1a2027;">
          <sc-for list="{{ historyEntries }}" as="entry" hint-placeholder-count="2">
            <article style="display:grid;gap:7px;padding-bottom:12px;border-bottom:1px solid #1a2027;">
              <span style="font-size:0.7rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;color:#d6bd7a;">{{ entry.label }}</span>
              <strong style="font-size:0.88rem;color:#c7cfd8;line-height:1.45;">{{ entry.headline }}</strong>
              <p style="margin:0;color:#aab4bf;font-size:0.84rem;line-height:1.5;">{{ entry.details }}</p>
              <sc-if value="{{ entry.sourceIsLink }}" hint-placeholder-val="{{ false }}"><a href="{{ entry.sourceUrl }}" target="_blank" rel="noopener" style="font-size:0.82rem;font-weight:600;">{{ entry.sourceLabel }}</a></sc-if>
              <sc-if value="{{ entry.sourceIsText }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#8a94a0;font-size:0.78rem;">Source: {{ entry.sourceLabel }}</p></sc-if>
            </article>
          </sc-for>
          <sc-if value="{{ historyHasMissingScope }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#8a94a0;font-size:0.78rem;">{{ historyMissingLabel }}</p></sc-if>
          <p style="margin:0;color:#6f7a86;font-size:0.7rem;">DRAFT — Verify all references against current official sources before acting.</p>
        </div>
      </details>
```

Keep the outer `historyVisible` condition so the card is hidden only when both scopes are empty.

- [ ] **Step 8: Apply and verify the compiled bundle patch**

Run:

```powershell
uv run python scripts/patch_dashboard_bundle.py --check
uv run python scripts/patch_dashboard_bundle.py
uv run python scripts/patch_dashboard_bundle.py --check
```

Expected: the first check reports the new patches apply cleanly, the write reports post-write verification success, and the final check reports all patches already applied/clean.

- [ ] **Step 9: Run dashboard bundle, patcher, and API tests**

Run:

```powershell
uv run pytest tests/test_dashboard.py::test_dashboard_patcher_accepts_fresh_or_legacy_source_text tests/test_dashboard.py::test_dashboard_bundle_renders_dual_history_from_workspace_data tests/test_dashboard.py::test_demo_dashboard_data_route_returns_workspace_payload tests/test_dashboard.py::test_personal_dashboard_data_route_returns_consolidated_payload -q
```

Expected: all four tests pass.

- [ ] **Step 10: Commit the dashboard presentation**

```powershell
git add scripts/patch_dashboard_bundle.py app/static/dashboard/index.html tests/test_dashboard.py
git commit -m "feat: render dual today in history"
```

---

### Task 5: Cohesion and Full Validation

**Files:**
- Modify only files already in scope if validation exposes a defect caused by Tasks 1–4.
- Test: `tests/test_history_import.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: the completed scoped selector, catalogs, dashboard contract, and compiled UI.
- Produces: a repository-validated feature with no unrelated staged changes.

- [ ] **Step 1: Verify obsolete fallback behavior is gone from active callers**

Run:

```powershell
rg -n "get_or_random|data\.today_in_history|historySpotlight|History spotlight" app tests scripts --glob '!app/static/dashboard/index.html'
```

Expected: no active dashboard/service caller uses `get_or_random`, and only intentional compatibility/schema references to `today_in_history` remain.

- [ ] **Step 2: Run focused history/dashboard tests**

```powershell
uv run pytest tests/test_history_import.py tests/test_dashboard.py -q
```

Expected: all focused tests pass.

- [ ] **Step 3: Run the complete test suite**

```powershell
uv run pytest tests/ -q
```

Expected: all tests pass.

- [ ] **Step 4: Run static validation**

```powershell
uv run mypy app tests
uv run ruff check .
```

Expected: both commands exit successfully with no errors.

- [ ] **Step 5: Inspect the final diff and staged scope**

```powershell
git diff --check
git status --short
git log --oneline -5
```

Expected: no whitespace errors; only the known pre-existing unrelated files remain modified outside the committed history work.

- [ ] **Step 6: Commit any validation-only correction**

Only if Steps 1–5 required an in-scope correction:

```powershell
git add app/schemas/history.py app/services/history/today_in_history.py app/services/history/catalog.py app/api/routes/history.py app/api/routes/dashboard.py app/schemas/dashboard.py data/seed/usmc_history_on_this_day.example.yaml data/seed/us_military_history_on_this_day.example.yaml scripts/patch_dashboard_bundle.py app/static/dashboard/index.html tests/test_history_import.py tests/test_dashboard.py
git commit -m "fix: complete dual history validation"
```

Do not create an empty commit.

---

DRAFT — Verify all references against current official sources before acting.
