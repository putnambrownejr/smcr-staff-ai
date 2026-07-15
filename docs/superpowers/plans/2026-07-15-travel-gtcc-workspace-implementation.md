# Travel and GTCC Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a user-driven Travel panel with trips, expense entries, receipt links, monthly GTCC checks, official links, and Chief of Staff visibility.

**Architecture:** Extend the existing `TravelCaseRecord` and `TravelCaseStore` so connector-created and manually created trips share one source of truth. Routes expose focused mutations; the dashboard calls those routes through reproducible decoded-bundle patches.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, JSON file stores, vanilla dashboard component bundle.

## Global Constraints

- UNCLASSIFIED only; never store card numbers, credentials, or bank exports.
- All balances and totals are visibly user-entered estimates.
- Every GTCC reminder includes official CitiManager and tracker links.
- Preserve connector-created travel cases and linked receipt behavior.

---

### Task 1: Travel ledger and GTCC domain model

**Files:**
- Modify: `app/schemas/travel_cases.py`
- Test: `tests/test_travel_case_store.py`

**Interfaces:**
- Produces: `TravelLedgerEntry`, `GtccCheckRecord`, `TravelCaseCreateRequest`, `TravelLedgerEntryRequest`, `GtccCheckRequest`, and summary properties on `TravelCaseRecord`.

- [ ] **Step 1: Write failing schema/store tests** covering manual trip creation, ledger totals, payment state, and monthly check freshness.
- [ ] **Step 2: Run** `uv run pytest tests/test_travel_case_store.py -q` and confirm the new tests fail because the interfaces are absent.
- [ ] **Step 3: Add models** with generated IDs, `Decimal` amounts, UTC timestamps, source=`user_entered`, and no credential/card fields.
- [ ] **Step 4: Run the focused tests** and confirm schema validation passes.
- [ ] **Step 5: Commit** `feat: extend travel cases with gtcc ledger`.

### Task 2: Store mutations and routes

**Files:**
- Modify: `app/services/connectors/travel_case_store.py`
- Modify: `app/api/routes/travel_cases.py`
- Test: `tests/test_travel_case_store.py`
- Test: `tests/test_travel_case_routes.py`

**Interfaces:**
- Produces: `create_case`, `add_ledger_entry`, `remove_ledger_entry`, `record_gtcc_check`, `delete_case`.
- Routes: `POST /travel-cases/{user_key}`, `POST/DELETE .../ledger`, `POST .../gtcc-checks`, `DELETE .../{trip_id}`.

- [ ] **Step 1: Add failing route tests** for user-key matching, unknown trips, valid entry/check persistence, and delete behavior.
- [ ] **Step 2: Run focused tests** and confirm 404/405 failures.
- [ ] **Step 3: Implement atomic record rewrites** using validated user keys and per-record UTC `updated_at`.
- [ ] **Step 4: Implement authenticated routes** with 400 for path/body user mismatch and 404 for missing records.
- [ ] **Step 5: Run** `uv run pytest tests/test_travel_case_store.py tests/test_travel_case_routes.py -q`.
- [ ] **Step 6: Commit** `feat: add travel ledger and gtcc check routes`.

### Task 3: Workspace Travel panel and monthly reminder

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Generated modify: `app/static/dashboard/index.html`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`

**Interfaces:**
- Consumes: Travel routes from Task 2.
- Produces: Workspace Travel panel, trip editor, ledger/check forms, CitiManager link, stale-data messaging.

- [ ] **Step 1: Add decoded-bundle assertions** for `Travel`, `/travel-cases/`, `Open CitiManager`, `Mark checked`, and user-entered warning.
- [ ] **Step 2: Add exact-match bundle patches** for state/load helpers, mutations, rendered panel, and reminder.
- [ ] **Step 3: Run** `uv run python scripts/patch_dashboard_bundle.py` and its `--check` mode.
- [ ] **Step 4: Run** `uv run pytest tests/test_dashboard.py tests/e2e/test_dashboard_flows.py -q`.
- [ ] **Step 5: Commit** `feat: add travel workspace panel`.

### Task 4: Chief brief integration

**Files:**
- Modify: `app/services/chief/orchestrator.py`
- Test: `tests/test_chief_orchestrator.py`

**Interfaces:**
- Consumes: enriched `TravelCaseRecord`.
- Produces: monthly check, stale trip, unlinked receipt, and user-entered outstanding balance prompts.

- [ ] **Step 1: Add failing Chief brief tests** for each prompt and confirm no claim of live bank connectivity.
- [ ] **Step 2: Implement action generation** using stored timestamps and current month.
- [ ] **Step 3: Run** `uv run pytest tests/test_chief_orchestrator.py -q`.
- [ ] **Step 4: Commit** `feat: surface gtcc checks in chief brief`.
