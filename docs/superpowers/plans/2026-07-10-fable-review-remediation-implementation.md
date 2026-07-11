# Fable Review Remediation Implementation Plan

Status: Implemented and verified on 2026-07-10.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every confirmed Fable review finding and make the repository's full pytest, mypy, Ruff, JavaScript, and browser quality gates pass.

**Architecture:** Apply small regression-tested fixes at the existing agent, preflight, route, audit-store, and dashboard boundaries. Carry warning-override authority as a validated result instead of trusting request data, retain conservative chain-call accounting as an upper bound, and close remaining strict-typing debt without changing unrelated runtime behavior.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, mypy strict mode, Ruff, vanilla ES modules, Playwright.

## Global Constraints

- UNCLASSIFIED only; do not add classified information, CUI, COMSEC, real frequencies, call signs, precise movements, sensitive operational details, or unnecessary PII.
- Detector findings remain advisory warnings, not classification determinations.
- Sanitized and original external sends remain available after current digest-bound acknowledgement.
- Audit and log recovery must never persist prompt text, response bodies, API keys, headers, or matched sensitive text.
- Preserve the existing public API fields; `expected_call_count` remains a conservative upper bound.
- Do not add dependencies or introduce an agent-capability registry refactor.
- Deliver all plan changes in one comprehensive follow-up commit to draft PR #26.

---

### Task 1: Make scenario detection token-aware

**Files:**
- Create: `tests/test_staff_scenario_detection.py`
- Modify: `app/services/agents/staff_advisor_agent.py:1-95`

**Interfaces:**
- Consumes: `_SCENARIO_SIGNALS`, `_COUNTRY_SIGNALS`, and user input text.
- Produces: `_contains_signal(text: str, signals: tuple[str, ...]) -> bool` and unchanged `_detect_scenario(input_text: str) -> bool`.

- [ ] **Step 1: Add false-positive and true-positive tests**

```python
import pytest

from app.services.agents.staff_advisor_agent import _detect_scenario


@pytest.mark.parametrize(
    "text",
    [
        "Help structure the support request for our next exercise.",
        "Review the broadcast plan for this exercise.",
        "Assess workmanship during the exercise.",
        "Plan an exercise near Indianapolis.",
    ],
)
def test_scenario_detection_rejects_substring_false_positives(text: str) -> None:
    assert _detect_scenario(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "Exercise in India after the port was damaged.",
        "Earthquake exercise with 500 displaced people and a damaged road.",
        "Training scenario in Japan with effects extending 20 km.",
    ],
)
def test_scenario_detection_accepts_complete_signals(text: str) -> None:
    assert _detect_scenario(text) is True
```

- [ ] **Step 2: Run the new tests and confirm the false positives fail**

Run: `uv run pytest tests/test_staff_scenario_detection.py -q`

Expected: the false-positive parameter cases fail because substring matching returns `True`.

- [ ] **Step 3: Implement escaped token-bound matching**

Add `import re`, then replace the membership checks with:

```python
def _contains_signal(text: str, signals: tuple[str, ...]) -> bool:
    return any(re.search(rf"(?<!\\w){re.escape(signal)}(?!\\w)", text) for signal in signals)


def _detect_scenario(input_text: str) -> bool:
    """Return True when the user input describes a specific scenario."""
    lowered = input_text.lower()
    has_scenario_signal = _contains_signal(lowered, _SCENARIO_SIGNALS)
    has_country = _contains_signal(lowered, _COUNTRY_SIGNALS)
    has_specifics = _contains_signal(
        lowered,
        (
            "magnitude",
            "category",
            "casualties",
            "displaced",
            "population",
            "km",
            "miles",
            "destroyed",
            "damaged",
            "airport",
            "port",
            "road",
        ),
    )
    return has_scenario_signal and (has_country or has_specifics)
```

- [ ] **Step 4: Run the focused tests**

Run: `uv run pytest tests/test_staff_scenario_detection.py tests/test_scenario_handoff.py -q`

Expected: all tests pass.

---

### Task 2: Derive warning override authority from validated preflight

**Files:**
- Modify: `app/services/llm_client.py:32-170`
- Modify: `app/services/agents/staff_advisor_agent.py:1285-1355`
- Modify: `app/services/agents/staff_advisor_agent.py:875-888`
- Modify: `app/services/agents/planning_advisor_agent.py:233-245`
- Modify: `app/services/agents/chief_of_staff_agent.py:180-192`
- Modify: `tests/test_llm_scenario_inference.py`
- Modify: `tests/test_external_processing.py`

**Interfaces:**
- Consumes: `ExternalProcessingPreflightService.authorize(...)` and its non-local `ApprovedExternalPayload` result.
- Produces: `ScenarioGenerationResult.warning_override_authorized: bool` and `ScenarioPopulation.allow_warning_override: bool`.

- [ ] **Step 1: Add regression tests for raw and validated acknowledgement**

Add a test proving a raw local-only acknowledgement does not authorize an override:

```python
def test_local_only_acknowledgement_does_not_authorize_warning_override() -> None:
    result = ScenarioGenerationResult(
        content=None,
        status=ScenarioGenerationStatus.local_only,
        preview=ExternalProcessingPreview(
            required=True,
            external_available=True,
            scope_label="agent:test",
        ),
        disclosure_mode=DisclosureMode.local_only,
    )

    assert result.warning_override_authorized is False
```

Extend the approved-original HTTP test to assert:

```python
assert generated.warning_override_authorized is True
```

Extend agent-level coverage so sensitive scenario text returns the validated external answer for an approved original/sanitized decision, while a caller-supplied local-only acknowledgement still receives the generic limited response.

- [ ] **Step 2: Run the focused tests and confirm the new attribute/behavior fails**

Run: `uv run pytest tests/test_llm_scenario_inference.py tests/test_external_processing.py -q`

Expected: failure because the validated-result flag does not exist and agents still inspect raw request acknowledgement.

- [ ] **Step 3: Add the validated result fields**

Update the immutable result types:

```python
@dataclass(frozen=True)
class ScenarioGenerationResult:
    content: str | None
    status: ScenarioGenerationStatus
    preview: ExternalProcessingPreview
    disclosure_mode: DisclosureMode | None = None
    warning_override_authorized: bool = False
```

```python
@dataclass(frozen=True)
class ScenarioPopulation:
    answer: str
    scenario_output: dict[str, object] | None = None
    status: ScenarioOutputStatus = ScenarioOutputStatus.not_applicable
    warnings: list[str] | None = None
    allow_warning_override: bool = False
```

Set `warning_override_authorized=True` only on generated and failed results reached after `authorize()` returned a non-local payload. Copy that flag into every `ScenarioPopulation` branch that uses the result.

- [ ] **Step 4: Replace all three raw acknowledgement checks**

In the staff, planning, and chief scenario response builders, use:

```python
allow_warning_override=population.allow_warning_override,
```

Remove the three `bool(context.external_processing_approval and ...acknowledged)` expressions.

- [ ] **Step 5: Run focused agent and external-processing tests**

Run: `uv run pytest tests/test_llm_scenario_inference.py tests/test_external_processing.py tests/test_scenario_handoff.py tests/test_chief_of_staff_agent.py -q`

Expected: all tests pass.

---

### Task 3: Improve external failure visibility and audit corruption recovery

**Files:**
- Modify: `app/services/llm_client.py:145-160`
- Modify: `app/services/external_processing/audit_store.py`
- Modify: `tests/test_external_processing.py`
- Modify: `tests/test_llm_scenario_inference.py`

**Interfaces:**
- Consumes: malformed audit JSON and approved HTTP exceptions.
- Produces: warning-level local logs and timestamped `*.corrupt-*.json` audit backups.

- [ ] **Step 1: Add logging and corruption regression tests**

```python
def test_corrupted_audit_file_is_quarantined_and_replaced(tmp_path: Path) -> None:
    store = ExternalProcessingAuditStore(tmp_path)
    path = store._path("capt-example")
    path.write_text("{broken", encoding="utf-8")

    assert store.get("capt-example").entries == []
    backups = list(tmp_path.glob(f"{path.stem}.corrupt-*.json"))
    assert len(backups) == 1

    store.append("capt-example", _audit_entry())
    assert len(store.get("capt-example").entries) == 1
```

Use `caplog.at_level(logging.WARNING)` around a mocked approved HTTP failure and assert the message `Approved LLM scenario call failed` appears without the synthetic prompt marker.

- [ ] **Step 2: Run tests and confirm audit parsing and log-level failures**

Run: `uv run pytest tests/test_external_processing.py tests/test_llm_scenario_inference.py -q`

Expected: malformed JSON raises a Pydantic validation error and the warning-level assertion fails.

- [ ] **Step 3: Implement bounded corruption recovery**

Add `datetime`, `UTC`, and `pydantic.ValidationError`, then implement:

```python
try:
    return ExternalProcessingAuditLog.model_validate_json(path.read_text(encoding="utf-8"))
except ValidationError:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(f"{path.stem}.corrupt-{timestamp}{path.suffix}")
    path.replace(backup)
    return ExternalProcessingAuditLog()
```

Do not catch `OSError`; permission and storage failures must remain visible.

- [ ] **Step 4: Raise the approved-call failure log level**

Replace:

```python
logger.debug("Approved LLM scenario call failed; falling back to template", exc_info=True)
```

with:

```python
logger.warning("Approved LLM scenario call failed; falling back to template", exc_info=True)
```

- [ ] **Step 5: Run focused tests**

Run: `uv run pytest tests/test_external_processing.py tests/test_llm_scenario_inference.py -q`

Expected: all tests pass and serialized audit assertions still prove no prompt content is stored.

---

### Task 4: Make preview counts honest, avoid no-key double execution, and deduplicate warnings

**Files:**
- Modify: `app/api/routes/agents.py`
- Modify: `app/services/external_processing/preflight.py`
- Modify: `app/static/dashboard/dashboard.js:3361-3430`
- Modify: `tests/test_external_processing.py`
- Modify: `tests/test_scenario_handoff.py`
- Modify: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: configured `Settings.llm_api_key`, requested chain steps, and repeated warning strings.
- Produces: unchanged `ExternalProcessingPreview` schema, upper-bound call language, and stable-order warning lists.

- [ ] **Step 1: Add route, warning, and copy regression tests**

Add a no-key preview test that patches the selected agent's `run` method and asserts it is not called:

```python
def test_no_key_preview_does_not_run_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()
    agent = agent_registry.get("planning-advisor")
    assert agent is not None
    run = MagicMock()
    monkeypatch.setattr(agent, "run", run)

    response = TestClient(app).post(
        "/agents/planning-advisor/external-processing-preview",
        json={"input": "Exercise in Japan.", "context": {}},
    )

    assert response.status_code == 200
    assert response.json()["required"] is False
    run.assert_not_called()
```

Add a chain test with duplicated baseline warnings and assert the returned warning list equals first-seen unique values. Add dashboard/static assertions for the literal `Up to` call-count label.

- [ ] **Step 2: Run the tests and confirm failures**

Run: `uv run pytest tests/test_external_processing.py tests/test_scenario_handoff.py tests/test_dashboard.py -q`

Expected: the agent is called during no-key preview, duplicate warnings remain, and the dashboard still says `Expected calls`.

- [ ] **Step 3: Short-circuit no-key preview routes**

At the start of both preview routes, use current settings:

```python
if not get_settings().llm_api_key:
    return _no_external_preview(scope_label, "No external LLM is configured; execution remains local-only.")
```

For a chain, compute the scope label from the ordered step IDs before returning.

- [ ] **Step 4: Deduplicate warnings in stable order**

Add:

```python
def _unique_warnings(warnings: list[str]) -> list[str]:
    return list(dict.fromkeys(warnings))
```

Apply it to both complete and early-stopped `ChainResponse` construction.

- [ ] **Step 5: Update call-count copy**

Change the dashboard summary fragment to:

```javascript
"Up to " + (preview.expected_call_count || 1) + " external calls",
```

Update multi-step preflight warning language to describe the number as a maximum, without renaming the API field.

- [ ] **Step 6: Run focused tests and JavaScript syntax validation**

Run: `uv run pytest tests/test_external_processing.py tests/test_scenario_handoff.py tests/test_dashboard.py -q`

Run: `node --check app/static/dashboard/dashboard.js`

Expected: all commands pass.

---

### Task 5: Remove approval-dialog listener accumulation

**Files:**
- Modify: `app/static/dashboard/dashboard.js:3400-3480`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`

**Interfaces:**
- Consumes: dialog cancel and disclosure-button events.
- Produces: one named cancel listener per dialog invocation, removed by every completion path.

- [ ] **Step 1: Add a static lifecycle contract test**

Extend the dashboard JavaScript test to assert the module contains both:

```python
assert 'dialog.addEventListener("cancel", onCancel' in script
assert 'dialog.removeEventListener("cancel", onCancel)' in script
```

Keep the existing E2E local-choice flow as the user-observable happy path.

- [ ] **Step 2: Run the static and E2E-local tests and confirm the static contract fails**

Run: `uv run pytest tests/test_dashboard.py -q`

Expected: failure because the current listener is anonymous and never removed on button completion.

- [ ] **Step 3: Implement symmetric listener cleanup**

Inside the Promise, use:

```javascript
const onCancel = (event) => {
  event.preventDefault();
  finish(null);
};
const finish = (decision) => {
  if (settled) return;
  settled = true;
  dialog.removeEventListener("cancel", onCancel);
  dialog.close();
  resolve(decision);
};
dialog.addEventListener("cancel", onCancel);
```

Keep button handlers and the `settled` guard unchanged.

- [ ] **Step 4: Run dashboard tests and syntax check**

Run: `uv run pytest tests/test_dashboard.py -q`

Run: `node --check app/static/dashboard/dashboard.js`

Expected: both pass.

---

### Task 6: Close every strict-mypy and Ruff baseline finding

**Files:**
- Modify: `pyproject.toml:48-66`
- Modify: `tests/e2e/conftest.py`
- Modify: `tests/e2e/test_dashboard_flows.py`
- Modify: `app/services/staff/billet_research_service.py`
- Modify: `tests/test_chief_of_staff_agent.py`
- Modify: `tests/test_modules.py`
- Modify: `tests/test_handoff_route.py`
- Modify: `tests/test_custom_mos_recipes.py`
- Modify: `tests/test_billet_research.py`
- Modify: `tests/test_auth.py`
- Modify: `app/services/agents/registry.py:1-30`

**Interfaces:**
- Consumes: the current 56-error mypy report and one-error Ruff report.
- Produces: zero-error `uv run mypy app tests` and `uv run ruff check .` without runtime behavior changes.

- [ ] **Step 1: Record the current failing baselines**

Run: `uv run mypy app tests`

Expected: 56 errors in nine files.

Run: `uv run ruff check .`

Expected: one I001 import-order error in `app/services/agents/registry.py`.

- [ ] **Step 2: Type the Playwright scaffold without weakening strict test checking**

Add this narrow import override:

```toml
[[tool.mypy.overrides]]
module = ["playwright.*"]
ignore_missing_imports = true
```

In the E2E files import `Generator` and `Any`. Use:

```python
def browser_page() -> Generator[Any, None, None]:
```

```python
def _expect(locator: Any) -> Any:
```

Annotate every E2E test as `(browser_page: Any) -> None`, the nested route callback as `(route: Any) -> None`, and `submitted_requests` as `list[dict[str, Any]]`.

- [ ] **Step 3: Add precise catalog types to billet research**

Define:

```python
from typing import TypedDict


class MosInfo(TypedDict):
    name: str
    navmc: str
    roles: list[str]
    doctrine: list[str]
    notes: str


class BilletInfo(TypedDict):
    title: str
    responsibilities: list[str]
    key_pubs: list[str]
```

All current catalog entries contain the declared keys. Change the catalogs and lookup return types to `dict[str, MosInfo]`, `dict[str, BilletInfo]`, `MosInfo | None`, and `BilletInfo | None`.

- [ ] **Step 4: Fix remaining test annotations and narrowing**

Apply these exact patterns:

```python
def _ctx(handoff: dict[str, object] | None = None) -> AgentContext:
```

```python
detail = d.get_pack("alpha-pack")
assert detail is not None
filenames = [item.filename for item in detail.files]
```

```python
def module_client(...) -> Generator[TestClient, None, None]:
def dashboard_client(...) -> Generator[TestClient, None, None]:
def client(...) -> Generator[TestClient, None, None]:
def reset_settings_cache() -> Generator[None, None, None]:
```

In `tests/test_custom_mos_recipes.py`, annotate `tmp_path: Path`, test returns `-> None`, and:

```python
def _override_store(tmp_path: Path) -> CustomMosRecipeStoreService:
```

- [ ] **Step 5: Correct registry import ordering**

Order agent imports alphabetically (`ace`, `artillery`, `assessment`, `base`, `checkin`, ...). Use Ruff's reported order; do not alter registry behavior.

- [ ] **Step 6: Run mypy and Ruff to confirm closure**

Run: `uv run mypy app tests`

Expected: `Success: no issues found in 362 source files`.

Run: `uv run ruff check .`

Expected: `All checks passed!`.

---

### Task 7: Run complete verification and reconcile the implementation record

**Files:**
- Modify: `docs/superpowers/plans/2026-07-10-fable-review-remediation-implementation.md`
- Modify: `docs/superpowers/specs/2026-07-10-fable-review-remediation-design.md`

**Interfaces:**
- Consumes: completed Tasks 1-6 and repository quality commands.
- Produces: a dated verification record and accepted-trade-off summary.

- [ ] **Step 1: Run the full non-browser suite**

Run: `uv run pytest tests/ -q -m "not e2e"`

Expected: all collected non-E2E tests pass.

- [ ] **Step 2: Run full static quality gates**

Run: `uv run mypy app tests`

Expected: success with zero errors.

Run: `uv run ruff check .`

Expected: all checks pass.

Run: `node --check app/static/dashboard/dashboard.js`

Run: `node --check app/static/dashboard/actions.js`

Expected: both exit zero.

- [ ] **Step 3: Run the browser suite with a bounded local server**

Start `uvicorn app.main:app --host 127.0.0.1 --port 8000` in a hidden process, run:

```powershell
uv run pytest -m e2e tests/e2e/ -q
```

Stop the server in a `finally` block.

Expected: all automated E2E tests pass; the intentionally manual server-down test remains skipped.

- [ ] **Step 4: Run diff and secret-scope integrity checks**

Run: `git diff --check`

Run a tracked-diff scan for key/token patterns and confirm only documented placeholders such as `sk-test` and `sk-your-key-here` appear.

Expected: no whitespace errors and no real credential material.

- [ ] **Step 5: Update plan/spec status with actual results**

Change the spec status to `Implemented and verified on 2026-07-10`. Add a `Verification Results` section to this plan containing the actual pass counts for pytest/E2E and the zero-error mypy/Ruff results. Do not claim a command passed unless its output was observed.

---

### Task 8: Publish one comprehensive follow-up commit

**Files:**
- Stage: every file modified by Tasks 1-7.

**Interfaces:**
- Consumes: a fully verified, reviewable working tree.
- Produces: one follow-up commit on `codex/external-processing-handoffs-actions` and an updated draft PR #26.

- [ ] **Step 1: Review final scope**

Run: `git status -sb`

Run: `git diff --stat`

Run: `git diff --check`

Expected: only remediation code, tests, typing fixes, and the design/plan documents are present.

- [ ] **Step 2: Stage the complete approved scope**

```powershell
git add app tests pyproject.toml docs/superpowers/specs/2026-07-10-fable-review-remediation-design.md docs/superpowers/plans/2026-07-10-fable-review-remediation-implementation.md
```

- [ ] **Step 3: Commit once, per the user's batching decision**

```powershell
git commit -m "Resolve external processing review findings"
```

- [ ] **Step 4: Push the tracked branch**

```powershell
git push origin codex/external-processing-handoffs-actions
```

- [ ] **Step 5: Verify PR #26 contains the commit**

Run: `gh pr view 26 --json url,isDraft,state,commits,headRefName,baseRefName`

Expected: draft PR #26 remains open against `main`, and its commit list includes `Resolve external processing review findings`.

## Verification Results

- `uv run pytest tests/ -q -m "not e2e"`: 531 passed, 8 deselected.
- `uv run pytest -m e2e tests/e2e/ -q`: 7 passed, 1 intentionally manual test skipped.
- `uv run mypy app tests`: success with no issues in 363 source files.
- `uv run ruff check .`: all checks passed.
- `node --check` passed for `dashboard.js` and `actions.js`.
- `git diff --check`: passed.
- Credential-shaped diff scan: no credential-shaped additions detected.

Accepted trade-offs remain unchanged: approval digests do not expire, configured-provider
previews still execute request-dependent scenario detection, and
`expected_call_count` remains a conservative maximum displayed as `Up to N external calls`.

DRAFT — Verify all references against current official sources before acting.
