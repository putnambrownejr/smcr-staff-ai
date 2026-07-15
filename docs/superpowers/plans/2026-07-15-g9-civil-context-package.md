# G-9 Civil Context Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the event-scoped G-9 planning API with source-aware infrastructure-dependency and cultural-context sections for domestic-support and overseas/partner exercises.

**Architecture:** Keep `POST /staff/g9-plan` and the stateless `G9Planner`. Expand the Pydantic contract with bounded input/output models; the planner builds tailored sections and evidence classifications without persistence or source retrieval.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, mypy, Ruff.

## Global Constraints

- UNCLASSIFIED, advisory-only, request-scoped behavior. No persistence, migrations, background jobs, external fetches, or new dependencies.
- Do not accept or generate precise locations, exploitable infrastructure vulnerabilities, sensitive movement details, COMSEC, targeting support, population profiling, or unnecessary PII.
- Preserve minimal existing `G9PlanningRequest` payloads: `operating_context` is optional; tailored output requires `domestic_support` or `overseas_partner`.
- Preserve the five existing response sections and `warnings`.
- Evidence rows explicitly distinguish reported fact, analytic inference, planning assumption, and synthetic exercise content.
- Use `DEFAULT_WARNINGS` and G-9-specific verification language. Do not make legal or authority determinations.

---

## File Structure

- Modify: `app/schemas/staff.py` — typed G-9 source/context/input/evidence models and expanded request/response contracts.
- Modify: `app/services/staff/g9_planner.py` — pure context, evidence, infrastructure, culture, and outline builders.
- Create: `tests/test_g9_planner.py` — schema and service behavior tests.
- Modify: `tests/test_new_staff_routes.py` — authenticated FastAPI regression tests.
- Do not modify `app/api/routes/staff.py` unless tests show a real schema/serialization defect; its existing route is already the correct integration point.

## Task 1: Add the typed request and response contract

**Files:**

- Modify: `app/schemas/staff.py:253-270`
- Create: `tests/test_g9_planner.py`

**Interfaces:**

- Consumes: `G9PlanningRequest` and `G9PlanningResponse`.
- Produces: `G9OperatingContext`, `G9SourceItem`, `G9InfrastructureSystem`, `G9CulturalContextItem`, `G9EvidenceKind`, `G9EvidenceAssessment`, and expanded G-9 models.

- [ ] **Step 1: Write failing schema tests**

~~~python
from pydantic import ValidationError
import pytest

from app.schemas.staff import G9OperatingContext, G9PlanningRequest


def test_g9_request_accepts_typed_civil_context_inputs() -> None:
    request = G9PlanningRequest(
        title="County support exercise",
        supported_problem="Plan civil-military coordination for a hurricane exercise.",
        operating_context=G9OperatingContext.domestic_support,
        source_items=[
            {
                "title": "County emergency plan",
                "claim": "The county publishes a shelter coordination process.",
                "source_type": "local-government",
                "corroborated": True,
            }
        ],
        infrastructure_systems=[
            {"system": "water", "condition_or_concern": "Continuity during storm response"}
        ],
        cultural_context_items=[
            {
                "documented_context": "Use accessible public-information formats.",
                "planning_relevance": "Coordinate accessible public information.",
            }
        ],
    )

    assert request.operating_context is G9OperatingContext.domestic_support
    assert request.infrastructure_systems[0].system == "water"


def test_g9_request_rejects_blank_required_civil_context_fields() -> None:
    with pytest.raises(ValidationError):
        G9PlanningRequest(
            title="Exercise",
            supported_problem="Support a civil-military exercise.",
            infrastructure_systems=[{"system": ""}],
        )
~~~

- [ ] **Step 2: Run the test and verify it fails**

Run: `uv run pytest tests/test_g9_planner.py -q`

Expected: FAIL during collection because the new models are undefined.

- [ ] **Step 3: Add minimal typed models**

Add before `G9PlanningRequest`:

~~~python
class G9OperatingContext(StrEnum):
    domestic_support = "domestic_support"
    overseas_partner = "overseas_partner"


class G9SourceItem(BaseModel):
    title: str = Field(min_length=1)
    url: str | None = None
    publisher: str | None = None
    retrieved_at: str | None = None
    claim: str | None = None
    source_type: str | None = None
    corroborated: bool = False


class G9InfrastructureSystem(BaseModel):
    system: str = Field(min_length=1)
    condition_or_concern: str | None = None
    known_dependency: str | None = None
    source_label: str | None = None


class G9CulturalContextItem(BaseModel):
    documented_context: str = Field(min_length=1)
    source_label: str | None = None
    regional_variation: str | None = None
    planning_relevance: str | None = None


class G9EvidenceKind(StrEnum):
    reported_fact = "reported_fact"
    analytic_inference = "analytic_inference"
    planning_assumption = "planning_assumption"
    synthetic_exercise_content = "synthetic_exercise_content"


class G9EvidenceAssessment(BaseModel):
    kind: G9EvidenceKind
    statement: str
    source_label: str | None = None
    source_date: str | None = None
    confidence: str
    verification_note: str
~~~

Expand the existing request and response without changing their current fields:

~~~python
class G9PlanningRequest(BaseModel):
    # existing fields
    operating_context: G9OperatingContext | None = None
    source_items: list[G9SourceItem] = Field(default_factory=list)
    infrastructure_systems: list[G9InfrastructureSystem] = Field(default_factory=list)
    cultural_context_items: list[G9CulturalContextItem] = Field(default_factory=list)


class G9PlanningResponse(BaseModel):
    # existing fields
    operating_context_frame: list[str] = Field(default_factory=list)
    infrastructure_dependency_assessment: list[str] = Field(default_factory=list)
    cultural_context_assessment: list[str] = Field(default_factory=list)
    evidence_and_assumptions: list[G9EvidenceAssessment] = Field(default_factory=list)
    civil_estimate_outline: list[str] = Field(default_factory=list)
~~~

- [ ] **Step 4: Run the schema tests**

Run: `uv run pytest tests/test_g9_planner.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add app/schemas/staff.py tests/test_g9_planner.py
git commit -m "feat: add G9 civil context schemas"
~~~

## Task 2: Build the event-scoped G-9 sections

**Files:**

- Modify: `app/services/staff/g9_planner.py:1-61`
- Modify: `tests/test_g9_planner.py`

**Interfaces:**

- Consumes: The Task 1 types and `DEFAULT_WARNINGS`.
- Produces: populated `operating_context_frame`, `infrastructure_dependency_assessment`, `cultural_context_assessment`, `evidence_and_assumptions`, and `civil_estimate_outline`.

- [ ] **Step 1: Write failing service tests**

~~~python
from app.schemas.staff import G9OperatingContext, G9PlanningRequest
from app.services.staff.g9_planner import G9Planner


def test_g9_planner_builds_domestic_civil_context_sections() -> None:
    response = G9Planner().build(
        G9PlanningRequest(
            title="County support exercise",
            supported_problem="Coordinate civil support in a hurricane exercise.",
            operating_context=G9OperatingContext.domestic_support,
            source_items=[
                {
                    "title": "County plan",
                    "claim": "The county publishes a shelter coordination process.",
                    "source_type": "local-government",
                    "corroborated": True,
                }
            ],
            infrastructure_systems=[
                {"system": "water", "known_dependency": "power continuity"}
            ],
            cultural_context_items=[
                {
                    "documented_context": "Use accessible public-information formats.",
                    "regional_variation": "Confirm language needs with local partners.",
                }
            ],
        )
    )

    assert any("civilian lead" in item.lower() for item in response.operating_context_frame)
    assert any("water" in item.lower() for item in response.infrastructure_dependency_assessment)
    assert any("variation" in item.lower() for item in response.cultural_context_assessment)
    assert response.evidence_and_assumptions[0].kind == "reported_fact"
    assert len(response.civil_estimate_outline) == 8


def test_g9_planner_marks_unsourced_claim_as_assumption() -> None:
    response = G9Planner().build(
        G9PlanningRequest(
            title="Partner exercise",
            supported_problem="Prepare civil-military context.",
            operating_context=G9OperatingContext.overseas_partner,
            source_items=[{"title": "Unattributed note", "claim": "A local service may be constrained."}],
        )
    )

    assert response.evidence_and_assumptions[0].kind == "planning_assumption"
    assert response.evidence_and_assumptions[0].confidence == "low"


def test_g9_planner_keeps_legacy_request_valid_and_flags_context_gap() -> None:
    response = G9Planner().build(
        G9PlanningRequest(title="Legacy request", supported_problem="Prepare a civil-military event.")
    )

    assert response.operating_context_frame
    assert any("operating context" in item.lower() for item in response.information_requirements)
~~~

- [ ] **Step 2: Run the test and verify it fails**

Run: `uv run pytest tests/test_g9_planner.py -q`

Expected: FAIL because the new response fields are absent or empty.

- [ ] **Step 3: Implement pure planner helpers**

Have `G9Planner.build()` call these helpers after assembling the current five sections:

~~~python
operating_context_frame = _operating_context_frame(request.operating_context)
infrastructure_dependency_assessment = _infrastructure_assessment(request.infrastructure_systems)
cultural_context_assessment = _cultural_context_assessment(request.cultural_context_items)
evidence_and_assumptions = _evidence_assessments(request.source_items)
civil_estimate_outline = _civil_estimate_outline(request)
~~~

Implement the following exact behavior:

- `_operating_context_frame(None)`: generic frame and a prompt to confirm context. Add the same gap to `information_requirements`.
- `domestic_support`: civilian lead, emergency-management coordination, and authority confirmation. Do not determine authority.
- `overseas_partner`: host-nation/embassy channels, partner/NGO independence, agreements, and releasability confirmation. Do not determine agreement status.
- Empty infrastructure input: return broad system categories (water, power, transport, communications, health, fuel, shelter, waste) and a research gap. Supplied entries may mention only submitted category, concern, dependency, source label, civil-effect question, and coordination question.
- Empty cultural input: return prompts for documented context, variation, engagement relevance, and assumptions to avoid. Supplied entries retain stated variation/relevance and do not predict group behavior.
- A source is `reported_fact` only with claim + source type + corroboration. Any claimed item missing those conditions is a low-confidence `planning_assumption` with a validation note. A title-only item is a low-confidence evidence gap, not a new factual assertion.
- The civil estimate has exactly these eight headings: event/context; civil situation/actors; infrastructure/civil effects; cultural context/variation; authorities/coordination; judgments/assumptions/requirements; recommended actions/decision points; sources/confidence/verification.

Pass every result into the response while preserving the current title, existing sections, and warnings.

- [ ] **Step 4: Run focused service verification**

Run: `uv run pytest tests/test_g9_planner.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add app/services/staff/g9_planner.py tests/test_g9_planner.py
git commit -m "feat: build G9 civil context package"
~~~

## Task 3: Cover the public API and prevent regressions

**Files:**

- Modify: `tests/test_new_staff_routes.py`

**Interfaces:**

- Consumes: The existing authenticated test fixture and `POST /staff/g9-plan` at `app/api/routes/staff.py:149-151`.
- Produces: JSON-contract tests. No route-code change is expected.

- [ ] **Step 1: Write failing API tests**

~~~python
def test_g9_plan_returns_source_aware_domestic_civil_context_package() -> None:
    response = TestClient(app).post(
        "/staff/g9-plan",
        headers=HEADERS,
        json={
            "title": "County support exercise",
            "supported_problem": "Coordinate civil support for a hurricane exercise.",
            "operating_context": "domestic_support",
            "source_items": [
                {
                    "title": "County emergency plan",
                    "claim": "The county publishes a shelter coordination process.",
                    "source_type": "local-government",
                    "corroborated": True,
                }
            ],
            "infrastructure_systems": [{"system": "water", "known_dependency": "power continuity"}],
            "cultural_context_items": [{"documented_context": "Use accessible public-information formats."}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["operating_context_frame"]
    assert payload["infrastructure_dependency_assessment"]
    assert payload["cultural_context_assessment"]
    assert payload["evidence_and_assumptions"][0]["kind"] == "reported_fact"
    assert len(payload["civil_estimate_outline"]) == 8


def test_g9_plan_keeps_legacy_minimal_payload_valid() -> None:
    response = TestClient(app).post(
        "/staff/g9-plan",
        headers=HEADERS,
        json={"title": "Legacy G9 request", "supported_problem": "Prepare civil-military planning support."},
    )

    assert response.status_code == 200
    assert response.json()["civil_situation_frame"]
    assert response.json()["operating_context_frame"]
~~~

- [ ] **Step 2: Run the focused API test**

Run: `uv run pytest tests/test_new_staff_routes.py -q`

Expected: PASS after Tasks 1–2; FAIL beforehand on the new response-field assertions.

- [ ] **Step 3: Keep the route thin**

Keep this route unchanged unless the test proves an actual schema/serialization issue:

~~~python
@router.post("/g9-plan", response_model=G9PlanningResponse)
def build_g9_plan(request: G9PlanningRequest) -> G9PlanningResponse:
    return _g9_planner.build(request)
~~~

Correct any failure in the schema or planner; do not create another route or bypass Pydantic validation.

- [ ] **Step 4: Run combined feature tests**

Run: `uv run pytest tests/test_g9_planner.py tests/test_new_staff_routes.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

~~~bash
git add tests/test_new_staff_routes.py
git commit -m "test: cover G9 civil context API"
~~~

## Task 4: Validate the complete implementation

**Files:**

- Modify: `docs/superpowers/specs/2026-07-15-g9-civil-context-package-design.md` only if final behavior differs from the approved contract.

- [ ] **Step 1: Check implementation-to-spec coverage**

Confirm each mapping before release:

~~~text
event-scoped/no storage -> no store calls in planner or route
two tailored contexts -> service and route tests
public-source provenance -> G9SourceItem + evidence tests
bounded infrastructure/culture -> schema + service tests
legacy compatibility -> service + route tests
worksheet + eight-heading estimate -> service + route tests
~~~

- [ ] **Step 2: Run the quality gate**

Run: `uv run pytest tests/ -q`

Expected: PASS.

Run: `uv run mypy app tests`

Expected: PASS with no new errors.

Run: `uv run ruff check .`

Expected: PASS with no new violations.

- [ ] **Step 3: Reconcile documentation only if needed**

If a verified implementation detail diverges from the approved design, update the exact affected section in the design file. Do not add unrelated roadmap work. If no divergence exists, make no doc change.

- [ ] **Step 4: Commit any documentation reconciliation**

~~~bash
git add docs/superpowers/specs/2026-07-15-g9-civil-context-package-design.md
git commit -m "docs: reconcile G9 civil context design"
~~~

Run this commit only if Step 3 changed the design.

## Plan Self-Review

- Spec coverage: Tasks 1–3 cover inputs, outputs, domestic/overseas framing, source classification, safety boundaries, and legacy compatibility. Task 4 validates the full quality gate and design alignment.
- Placeholder scan: Every task names concrete files, interfaces, test code, commands, and expected outcomes.
- Type consistency: Task 1 defines the types consumed by Task 2; Task 2 returns only Task 1 response fields; Task 3 tests serialization through the existing FastAPI route.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-15-g9-civil-context-package.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session in batches with checkpoints for review.

Which approach?

