# FitRep Profile and Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support reviewed record/RS-profile imports, manual entry, transparent analytics, and improvement tracking under a selected Reporting Senior.

**Architecture:** A dedicated file-per-user FitRep store keeps reports, RS snapshots, and goals. The import service parses existing local-context previews into proposals; only explicit confirmation persists data. Analytics are deterministic and return chart-ready series plus data-quality warnings.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, JSON file store, existing PDF/DOCX/text extraction, vanilla dashboard.

## Global Constraints

- Imports never save or overwrite silently.
- Preserve source context ID and uncertainty notes.
- Analytics are descriptive; never predict selection or promotion.
- Charts expose exact values in text/table equivalents.

---

### Task 1: FitRep schemas and store

**Files:**
- Create: `app/schemas/fitreps.py`
- Create: `app/services/fitreps/store.py`
- Create: `app/services/fitreps/__init__.py`
- Modify: `app/core/config.py`
- Test: `tests/test_fitrep_store.py`

**Interfaces:**
- Produces: `FitrepReport`, `RsProfileSnapshot`, `FitrepImprovementGoal`, request models, `FitrepWorkspace`, and `FitrepStore.get/upsert_report/add_rs_snapshot/upsert_goal/delete_report`.

- [ ] **Step 1: Write failing store tests** for user isolation, manual records, append-only RS snapshots, goals, and deletion.
- [ ] **Step 2: Run** `uv run pytest tests/test_fitrep_store.py -q` and confirm import failures.
- [ ] **Step 3: Implement schemas and SHA-256 user-key store** with UTC timestamps and stable generated IDs.
- [ ] **Step 4: Add `fitrep_storage_dir`** to settings and configured directories.
- [ ] **Step 5: Run focused tests** and commit `feat: add fitrep profile store`.

### Task 2: Reviewed import proposals

**Files:**
- Create: `app/services/fitreps/importer.py`
- Test: `tests/test_fitrep_importer.py`

**Interfaces:**
- Produces: `propose_report_import(text, context_id)` and `propose_rs_profile_import(text, context_id)` returning typed proposals with warnings and provenance.

- [ ] **Step 1: Add fixture-based failing tests** for labeled dates, RS name, relative value, trait rows, ambiguous fields, and sparse documents.
- [ ] **Step 2: Implement conservative label/line parsing** without inventing missing values.
- [ ] **Step 3: Run** `uv run pytest tests/test_fitrep_importer.py -q`.
- [ ] **Step 4: Commit** `feat: propose fitrep profile imports`.

### Task 3: Analytics service and API

**Files:**
- Create: `app/services/fitreps/analytics.py`
- Create: `app/api/routes/fitreps.py`
- Modify: `app/main.py`
- Test: `tests/test_fitrep_analytics.py`
- Test: `tests/test_fitrep_routes.py`

**Interfaces:**
- Routes: workspace CRUD, import preview from `context_id`, confirmation save, and `GET /fitreps/{user_key}/analytics`.
- Produces analytics series for RV, traits, RS grouping, comparative assessment, sample size, and data quality.

- [ ] **Step 1: Add failing analytics and route tests** including no-data and small-sample warnings.
- [ ] **Step 2: Implement deterministic calculations** with explicit counts and no predictive language.
- [ ] **Step 3: Implement authenticated routes** using `LocalContextStore.read_preview` for proposal endpoints.
- [ ] **Step 4: Register the router** and run focused tests.
- [ ] **Step 5: Commit** `feat: add fitrep imports and analytics api`.

### Task 4: FitReps dashboard experience

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Generated modify: `app/static/dashboard/index.html`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`

**Interfaces:**
- Consumes: FitRep routes from Task 3 and existing counseling relationships.
- Produces: upload/review/manual paths, analytics cards/plots with tables, RS filter, and goal editor.

- [ ] **Step 1: Add bundle/browser assertions** for both uploads, manual input, analytics labels, source review, and counseling navigation.
- [ ] **Step 2: Add idempotent decoded-bundle patches** for fetch helpers, forms, review state, and accessible SVG/table summaries.
- [ ] **Step 3: Regenerate and dry-check the bundle**.
- [ ] **Step 4: Run focused dashboard tests**.
- [ ] **Step 5: Commit** `feat: add fitrep analytics workspace`.
