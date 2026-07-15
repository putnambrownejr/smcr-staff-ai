# Chief of Staff Capability Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the Chief of Staff read approved application domains and perform explicit append operations with audit and Undo, without arbitrary filesystem writes.

**Architecture:** A typed gateway composes existing stores and new Travel/FitRep/Cadence stores. Capability requests use a closed operation enum. Every write records a local audit snapshot and returns an undo token consumed by a dedicated endpoint.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, local JSON audit store.

## Global Constraints

- No shell capability or generic filesystem writer.
- Repository search is read-only and root-scoped with exclusions.
- Inferred imports remain proposals; replacement/delete/external operations require confirmation.
- Explicit append operations identify the affected record and return Undo.

---

### Task 1: Capability schemas, audit store, and repository reader

**Files:**
- Create: `app/schemas/chief_capabilities.py`
- Create: `app/services/chief/capability_gateway.py`
- Create: `app/services/chief/capability_audit_store.py`
- Modify: `app/core/config.py`
- Test: `tests/test_chief_capability_gateway.py`

**Interfaces:**
- Produces: closed read/append operation enums, `ChiefCapabilityRequest/Response`, `UndoRequest`, `ChiefCapabilityGateway.execute/undo/search_repository`.

- [ ] **Step 1: Write failing tests** for domain summaries, explicit append, audit creation, single-use Undo, path exclusions, and traversal rejection.
- [ ] **Step 2: Implement SHA-256 user-key audit storage** and repository-root path validation.
- [ ] **Step 3: Implement typed operations** for travel entries/checks, FitRep records/goals, and cadences.
- [ ] **Step 4: Run focused tests** and commit `feat: add chief capability gateway`.

### Task 2: Chief routes and brief awareness

**Files:**
- Modify: `app/api/routes/chief.py`
- Modify: `app/schemas/chief.py`
- Modify: `app/services/chief/orchestrator.py`
- Test: `tests/test_chief_routes.py`
- Test: `tests/test_chief_orchestrator.py`

**Interfaces:**
- Routes: `POST /chief/capabilities`, `POST /chief/capabilities/undo`, `GET /chief/capabilities/{user_key}/summary`.

- [ ] **Step 1: Add failing authenticated route tests** for read, append, validation, and Undo.
- [ ] **Step 2: Wire gateway dependencies** from configured stores.
- [ ] **Step 3: Add capability summary to Chief brief** without including full private document content.
- [ ] **Step 4: Run focused tests** and commit `feat: expose chief domain capabilities`.

### Task 3: Chief agent contract and documentation

**Files:**
- Modify: `app/services/agents/chief_of_staff_agent.py`
- Modify: `docs/agents_setup/staff_operating_model.md`
- Test: `tests/test_chief_of_staff_agent.py`

**Interfaces:**
- Produces: clear agent instructions naming available read/append/proposal/confirm/undo behavior.

- [ ] **Step 1: Add failing content tests** for typed capability language and prohibition on unrestricted filesystem writes.
- [ ] **Step 2: Update agent answer/follow-ups and operating model**.
- [ ] **Step 3: Run focused tests** and commit `docs: define chief capability operations`.
