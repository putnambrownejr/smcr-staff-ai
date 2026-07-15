# Leader, Fitness, Finance, and Cadence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bounded GTCC, Financial Readiness, Fitness Planning, and Warrior-Monk agents; expand Leadership Advisor with MLD; produce staff-reviewed unit PT/ORM plans; and add local creeds, oaths, and cadence libraries.

**Architecture:** Agent builders share curated official source packs. Unit PT uses a deterministic typed planning service and staff-review models. Built-in professional texts live in `docs/sources`; private cadences use a file-per-user store and authenticated API.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, local JSON stores, existing agent registry and scenario chain.

## Global Constraints

- Fitness supports 5–50 Marines and never claims FFI/medical authority.
- ORM output does not represent official risk acceptance.
- Financial Readiness and GTCC remain distinct.
- Adult cadences are opt-in and exclude slurs, harassment, hazing, sexual violence, and targeted degradation.
- Exact policy/creed/oath text is source-attributed and verification-dated.

---

### Task 1: Source packs and local reference documents

**Files:**
- Create: `docs/sources/marine_corps_creeds_and_oaths.md`
- Create: `docs/sources/marine_corps_cadences.md`
- Modify: `docs/sources/README.md`
- Modify: `app/services/agents/source_refs.py`
- Test: `tests/test_agent_content_reliability.py`

**Interfaces:**
- Produces: `FITNESS_REFERENCES`, `FINANCIAL_READINESS_REFERENCES`, `GTCC_REFERENCES`, `WARRIOR_MONK_REFERENCES`, and indexed local files.

- [ ] **Step 1: Add failing source-pack tests** for official URLs, local documents, and verification/footer text.
- [ ] **Step 2: Add source-attributed local content** from official/public-domain sources, keeping cadence text redistributable.
- [ ] **Step 3: Add source tuples** and run focused reliability tests.
- [ ] **Step 4: Commit** `docs: add creeds oaths and cadence sources`.

### Task 2: Cadence store and API

**Files:**
- Create: `app/schemas/cadences.py`
- Create: `app/services/fitness/cadence_store.py`
- Create: `app/services/fitness/__init__.py`
- Create: `app/api/routes/cadences.py`
- Modify: `app/core/config.py`
- Modify: `app/main.py`
- Test: `tests/test_cadence_store.py`
- Test: `tests/test_cadence_routes.py`

**Interfaces:**
- Produces user-key CRUD and combined built-in/private listing with content ratings.

- [ ] **Step 1: Write failing CRUD, user-isolation, and content-boundary tests**.
- [ ] **Step 2: Implement file-per-user cadence storage** and conservative prohibited-content validation.
- [ ] **Step 3: Implement authenticated routes and register them**.
- [ ] **Step 4: Run focused tests** and commit `feat: add private cadence library`.

### Task 3: Typed unit PT and ORM planning

**Files:**
- Create: `app/schemas/fitness.py`
- Create: `app/services/fitness/unit_pt_planner.py`
- Create: `app/api/routes/fitness.py`
- Modify: `app/schemas/scenario_handoff.py`
- Modify: `app/main.py`
- Test: `tests/test_unit_pt_planner.py`
- Test: `tests/test_fitness_routes.py`
- Modify: `tests/test_scenario_handoff.py`

**Interfaces:**
- Produces: `UnitPtPlanRequest`, `UnitPtPlan`, `StaffPtReview`, `OrmMatrix`, typed OpsO/SEL/ORM/Fitness scenario outputs, and `POST /fitness/unit-pt/plan`.

- [ ] **Step 1: Add failing tests** for counts 4/5/12/13/24/25/50/51, scaling bands, staff reviews, hazard controls, cadence preference, and partial constraints.
- [ ] **Step 2: Implement deterministic plan construction** with editable heuristics and explicit source/safety warnings.
- [ ] **Step 3: Extend scenario output union/map** with typed roles.
- [ ] **Step 4: Add and register the route**, then run focused tests.
- [ ] **Step 5: Commit** `feat: add staff reviewed unit pt planner`.

### Task 4: Specialist agents and MLD separation

**Files:**
- Create: `app/services/agents/readiness_development_agents.py`
- Modify: `app/services/agents/leadership_agent.py`
- Modify: `app/services/agents/registry.py`
- Test: `tests/test_agent_registry.py`
- Test: `tests/test_agent_content_reliability.py`

**Interfaces:**
- Produces agents `gtcc-advisor`, `financial-readiness-advisor`, `fitness-planning-advisor`, `warrior-monk`; preserves `leadership-advisor`.

- [ ] **Step 1: Add failing registry/category/content tests** for IDs, separation, source packs, limitations, MLD six areas, cadence questions, and PT staff handoffs.
- [ ] **Step 2: Implement four bounded agent builders**; Fitness invokes the typed planner when structured input is provided.
- [ ] **Step 3: Expand Leadership Advisor** with practical MLD ownership and Warrior-Monk handoff language.
- [ ] **Step 4: Register/categories agents** and run focused tests.
- [ ] **Step 5: Commit** `feat: add readiness development agents`.

### Task 5: Dashboard and full cohesion gate

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Generated modify: `app/static/dashboard/index.html`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`
- Modify: `docs/API_REFERENCE.md`

**Interfaces:**
- Produces cadence management access, unit PT planning entry point, all new AI cards/IDs, and documented APIs.

- [ ] **Step 1: Add dashboard/API documentation assertions**.
- [ ] **Step 2: Patch and regenerate the dashboard** with accessible forms, status states, and external-source labels.
- [ ] **Step 3: Run all focused browser and API tests**.
- [ ] **Step 4: Run** `uv run pytest tests/ -q`, `uv run mypy app tests`, and `uv run ruff check .`.
- [ ] **Step 5: Perform desktop/browser cohesion review**, fix discovered defects, rerun the full gate, and commit `feat: complete readiness development suite`.
