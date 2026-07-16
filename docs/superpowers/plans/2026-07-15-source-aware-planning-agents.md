# Source-Aware Planning Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver four discoverable, source-aware planning specialists; add Red Team evidence/hypotheses modes and Assessment/Learning corrective-action outputs; validate safe, local-only chains.

**Architecture:** A typed `SourceSelection` enters agent and chain requests, then a local `SourceEvidenceResolver` converts approved Source Library chunks into `context.extra["source_evidence"]`. Four focused `Agent` implementations return strict scenario handoffs. Existing Red Team and Assessment/Learning agents consume the same resolved evidence and explicit mode options. The dashboard remains a catalog only; its existing `/agents` fetch automatically discovers the new registry records.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, existing flat-JSON Source Library store, pytest, mypy, Ruff.

## Global Constraints

- UNCLASSIFIED, public, local, training, or fictional content only.
- Do not fetch external content during agent or chain execution.
- Source selection requires `context.user_key`; local ownership is mandatory.
- Non-current sources are excluded unless `include_noncurrent` is explicitly true.
- Every agent remains advisory, citation-required, and human-review-required.
- Do not add a dashboard agent-execution interface.
- Every advisory answer includes `DRAFT — Verify all references against current official sources before acting.`

---

### Task 1: Typed local-source evidence resolution

**Files:**
- Create: `app/services/agents/source_context.py`
- Modify: `app/schemas/agents.py`
- Modify: `app/schemas/scenario_handoff.py`
- Modify: `app/api/routes/agents.py`
- Test: `tests/test_agent_source_context.py`

**Interfaces:**
- Produces `SourceSelection`, accepted by `AgentRunRequest` and `ChainRequest`.
- Produces `SourceEvidenceResolver.resolve(user_key: str, selection: SourceSelection) -> ResolvedSourceEvidence`.
- Produces normalized `context.extra["source_evidence"]: list[dict[str, str]]` and source-trust warnings.

- [ ] **Step 1: Write the failing source-resolution tests**

```python
def test_resolver_combines_explicit_and_query_hits_without_duplicates() -> None:
    resolved = resolver.resolve("owner", SourceSelection(source_ids=[source_id], query="bridge"))
    assert len({item["chunk_id"] for item in resolved.items}) == len(resolved.items)
    assert resolved.items[0]["source_hash"]

def test_noncurrent_source_requires_explicit_opt_in() -> None:
    excluded = resolver.resolve("owner", SourceSelection(source_ids=[watch_id]))
    included = resolver.resolve("owner", SourceSelection(source_ids=[watch_id], include_noncurrent=True))
    assert not excluded.items and excluded.warnings
    assert included.items and any("non-current" in warning.lower() for warning in included.warnings)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `uv run pytest tests/test_agent_source_context.py -q`

Expected: import failure for `SourceSelection` and `SourceEvidenceResolver`.

- [ ] **Step 3: Add request models and resolver**

```python
class SourceSelection(BaseModel):
    source_ids: list[str] = Field(default_factory=list, max_length=20)
    query: str | None = Field(default=None, max_length=500)
    limit: int = Field(default=6, ge=1, le=20)
    include_noncurrent: bool = False

class AgentRunRequest(BaseModel):
    input: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    source_selection: SourceSelection | None = None

class ResolvedSourceEvidence(BaseModel):
    items: list[dict[str, str]] = Field(default_factory=list)
    source_trust: list[SourceTrustMarker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

Implement `SourceEvidenceResolver` on `SourceLibraryStore.search()`. Validate every explicit ID with `store.get(user_key, source_id)`, reject absent or foreign IDs with `ValueError`, convert chunks to strings containing `title`, `publisher`, `url`, `retrieved_at`, `source_hash`, `chunk_id`, `excerpt`, and `trust_status`, and deduplicate by `chunk_id`.

In `_build_agent_context`, resolve only when a request has `source_selection`; require `user_key`; merge evidence under `extra["source_evidence"]`; append resolver warnings to the final route response. Apply the same resolver before each chain step so every step receives the same evidence.

- [ ] **Step 4: Run focused validation**

Run: `uv run pytest tests/test_agent_source_context.py tests/test_agents_route.py tests/test_scenario_handoff.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add app/schemas/agents.py app/schemas/scenario_handoff.py app/services/agents/source_context.py app/api/routes/agents.py tests/test_agent_source_context.py
git commit -m "feat: resolve local source evidence for agents"
```

### Task 2: Area Study Builder and structured handoff

**Files:**
- Create: `app/services/agents/area_study_agent.py`
- Modify: `app/schemas/scenario_handoff.py`
- Modify: `app/services/agents/registry.py`
- Test: `tests/test_area_study_agent.py`

**Interfaces:**
- Produces `AreaStudyScenarioOutput` with PMESII, ASCOPE, infrastructure/cultural factors, source gaps, and `role="area_study"`.
- Registers `area-study-builder`.

- [ ] **Step 1: Write failing behavior tests**

```python
def test_area_study_builder_labels_unsupplied_facts_as_gaps() -> None:
    response = agent.run("Build an area study for a training scenario.", AgentContext())
    assert "Evidence gaps" in response.answer
    assert response.scenario_output_status == ScenarioOutputStatus.validated

def test_area_study_builder_cites_resolved_local_evidence() -> None:
    response = agent.run("Assess the area.", context_with_source_evidence())
    assert any(c.source_hash for c in response.structured_citations)
```

- [ ] **Step 2: Implement the strict output and agent**

```python
class AreaStudyScenarioOutput(StrictScenarioModel):
    role: str = "area_study"
    operational_area: str = ""
    pmesii: dict[str, list[str]] = Field(default_factory=dict)
    ascope: AscopeEntry = Field(default_factory=AscopeEntry)
    infrastructure_and_culture: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
```

Render only supplied source excerpts as observations. Render missing PMESII/ASCOPE fields as collection gaps. Use the standard local evidence citation helper from Task 1 plus established public baseline references. End the answer with the exact draft warning.

- [ ] **Step 3: Register and validate**

Run: `uv run pytest tests/test_area_study_agent.py tests/test_agent_registry.py -q`

Expected: PASS and `agent_registry.get("area-study-builder")` is not `None`.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/area_study_agent.py app/schemas/scenario_handoff.py app/services/agents/registry.py tests/test_area_study_agent.py
git commit -m "feat: add area study builder agent"
```

### Task 3: Actor Network Analyst and Information Requirements Manager

**Files:**
- Create: `app/services/agents/actor_network_agent.py`
- Create: `app/services/agents/information_requirements_agent.py`
- Modify: `app/schemas/scenario_handoff.py`
- Modify: `app/services/agents/registry.py`
- Test: `tests/test_actor_network_agent.py`
- Test: `tests/test_information_requirements_agent.py`

**Interfaces:**
- Produces `ActorNetworkScenarioOutput` with organization-level actors, relationships, confidence, and gaps.
- Produces `InformationRequirementsScenarioOutput` with PIR/FFIR/CIR and decision linkage.
- Registers `actor-network-analyst` and `information-requirements-manager`.

- [ ] **Step 1: Write failing tests for boundary and output**

```python
def test_actor_network_excludes_individual_targeting() -> None:
    response = actor.run("Map named civilians for targeting.", AgentContext())
    assert response.confidence == Confidence.low
    assert any("sensitive" in warning.lower() for warning in response.warnings)

def test_information_manager_links_each_requirement_to_a_decision() -> None:
    response = irm.run("What must the commander know before a route decision?", AgentContext())
    requirements = response.scenario_output["requirements"]
    assert all(item["decision_supported"] for item in requirements)
```

- [ ] **Step 2: Implement both agents and models**

```python
class ActorNetworkScenarioOutput(StrictScenarioModel):
    role: str = "actor_network"
    actors: list[dict[str, str]] = Field(default_factory=list)
    relationships: list[dict[str, str]] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)

class InformationRequirement(StrictScenarioModel):
    category: str = "CIR"
    requirement: str = ""
    decision_supported: str = ""
    indicator: str = ""
    collection_question: str = ""
    recommended_owner: str = ""
    priority: str = ""
```

Use `prior_assessments["area_study"]` and `["actor_network"]` when present. Keep actors to organizations, institutions, and broad categories. Make every IR a human-reviewable recommendation, not a tasking order. Include the exact draft warning.

- [ ] **Step 3: Validate both agents**

Run: `uv run pytest tests/test_actor_network_agent.py tests/test_information_requirements_agent.py tests/test_agent_content_reliability.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/actor_network_agent.py app/services/agents/information_requirements_agent.py app/schemas/scenario_handoff.py app/services/agents/registry.py tests/test_actor_network_agent.py tests/test_information_requirements_agent.py
git commit -m "feat: add actor and information requirements agents"
```

### Task 4: IPB Assistant and full specialist chain

**Files:**
- Create: `app/services/agents/ipb_agent.py`
- Modify: `app/schemas/scenario_handoff.py`
- Modify: `app/services/agents/registry.py`
- Test: `tests/test_ipb_agent.py`
- Test: `tests/test_source_aware_planning_chain.py`

**Interfaces:**
- Produces `IpbScenarioOutput` with four-step IPB results, assumptions, indicators, and collection gaps.
- Registers `ipb-assistant`.
- Supports `area-study-builder -> actor-network-analyst -> information-requirements-manager -> ipb-assistant`.

- [ ] **Step 1: Write failing IPB and chain tests**

```python
def test_ipb_assistant_separates_evidence_assumptions_and_hypotheses() -> None:
    response = ipb.run("Build an IPB scaffold.", AgentContext())
    assert "Evidence" in response.answer
    assert "Assumptions" in response.answer
    assert "Hypotheses" in response.answer

def test_source_aware_specialist_chain_forwards_prior_assessments(client: TestClient) -> None:
    response = client.post("/agents/chain", json={"scenario": "Training scenario", "steps": STEPS})
    assert response.status_code == 200
    assert [row["agent_id"] for row in response.json()["results"]] == STEPS
```

- [ ] **Step 2: Implement IPB model, agent, and registry entry**

```python
class IpbScenarioOutput(StrictScenarioModel):
    role: str = "ipb"
    operational_environment: list[str] = Field(default_factory=list)
    environmental_effects: list[str] = Field(default_factory=list)
    broad_threat_or_hazard_patterns: list[str] = Field(default_factory=list)
    indicators_and_event_templates: list[str] = Field(default_factory=list)
    collection_gaps: list[str] = Field(default_factory=list)
```

Use prior area-study, actor-network, and IR outputs without inventing missing facts. For sensitive inputs, rely on the base generic-response safeguard. Include the exact draft warning.

- [ ] **Step 3: Validate chain and registration**

Run: `uv run pytest tests/test_ipb_agent.py tests/test_source_aware_planning_chain.py tests/test_scenario_handoff.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/ipb_agent.py app/schemas/scenario_handoff.py app/services/agents/registry.py tests/test_ipb_agent.py tests/test_source_aware_planning_chain.py
git commit -m "feat: add IPB assistant chain"
```

### Task 5: Red Team evidence and hypotheses modes

**Files:**
- Modify: `app/services/agents/red_team_agent.py`
- Modify: `app/schemas/agents.py`
- Test: `tests/test_red_team_modes.py`

**Interfaces:**
- `AgentRunRequest.options["mode"]` supports `assumptions`, `evidence`, or `hypotheses` for Red Team.
- Default remains `assumptions`.

- [ ] **Step 1: Write failing mode tests**

```python
@pytest.mark.parametrize("mode, heading", [
    ("assumptions", "What to challenge"),
    ("evidence", "Claim ledger"),
    ("hypotheses", "Competing hypotheses"),
])
def test_red_team_modes_are_distinct(mode: str, heading: str) -> None:
    response = agent.run("Test this planning claim.", AgentContext(extra={"agent_options": {"mode": mode}}))
    assert heading in response.answer
```

- [ ] **Step 2: Implement typed options and mode dispatch**

```python
class AgentRunRequest(BaseModel):
    input: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
```

Merge `options` into `AgentContext.extra["agent_options"]`. In Red Team, validate the three allowed mode values; unsupported values return a 422 API response. Evidence mode builds claims exclusively from local evidence when present and otherwise labels every entry as a collection need. Hypotheses mode emits competing explanations, support/refutation, discriminators, and confidence. Preserve the existing assumptions output as default. Include the draft warning in every mode.

- [ ] **Step 3: Validate regression behavior**

Run: `uv run pytest tests/test_red_team_modes.py tests/test_agent_registry.py tests/test_agent_content_reliability.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/red_team_agent.py app/schemas/agents.py tests/test_red_team_modes.py
git commit -m "feat: add red team evidence and hypotheses modes"
```

### Task 6: Assessment/Learning corrective-action register

**Files:**
- Modify: `app/services/agents/assessment_learning_agent.py`
- Test: `tests/test_assessment_learning_actions.py`

**Interfaces:**
- Adds `CorrectiveActionRecord` to the response scenario output with observation, measure, root cause, action, owner, suspense, and verification condition.

- [ ] **Step 1: Write failing follow-through tests**

```python
def test_assessment_agent_outputs_owned_measurable_correction() -> None:
    response = agent.run("AAR: radio checks were late and no owner was assigned.", AgentContext())
    assert "Corrective-action register" in response.answer
    assert "Next-drill verification condition" in response.answer

def test_assessment_agent_flags_missing_measure_or_owner() -> None:
    response = agent.run("Attendance was good.", AgentContext())
    assert "Missing evidence or ownership" in response.answer
```

- [ ] **Step 2: Implement the register**

```python
class CorrectiveActionRecord(StrictScenarioModel):
    observation: str = ""
    standard_or_measure: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    owner: str = "Human assignment required"
    suspense: str = "Human assignment required"
    next_drill_verification_condition: str = ""
```

Derive a conservative record from supplied input and evidence. Use explicit “not provided” labels for missing measure, owner, suspense, root cause, or verification data. Do not imply a correction is complete. End the response with the exact draft warning.

- [ ] **Step 3: Validate**

Run: `uv run pytest tests/test_assessment_learning_actions.py tests/test_agent_content_reliability.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/assessment_learning_agent.py tests/test_assessment_learning_actions.py
git commit -m "feat: add assessment corrective action register"
```

### Task 7: End-to-end acceptance and release gate

**Files:**
- Modify: `tests/test_agent_registry.py`
- Modify: `tests/test_agent_content_reliability.py`
- Modify: `tests/test_external_processing.py`
- Test: `tests/test_source_aware_planning_acceptance.py`

**Interfaces:**
- Locks catalog discovery, source trust behavior, specialist chain, local-only execution, safety degradation, and mode behavior.

- [ ] **Step 1: Add an end-to-end acceptance test**

```python
def test_source_aware_planning_workflow_is_local_safe_and_cited(client: TestClient) -> None:
    response = client.post("/agents/chain", json=source_aware_chain_payload())
    assert response.status_code == 200
    assert response.json()["completed"] is True
    assert all(step["response"]["human_review_required"] for step in response.json()["results"])
```

- [ ] **Step 2: Run all relevant tests**

Run: `uv run pytest tests/test_agent_source_context.py tests/test_area_study_agent.py tests/test_actor_network_agent.py tests/test_information_requirements_agent.py tests/test_ipb_agent.py tests/test_source_aware_planning_chain.py tests/test_red_team_modes.py tests/test_assessment_learning_actions.py tests/test_source_aware_planning_acceptance.py tests/test_agent_registry.py tests/test_agent_content_reliability.py tests/test_external_processing.py -q`

Expected: PASS.

- [ ] **Step 3: Run full release validation**

Run:

```powershell
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit**

```powershell
git add tests/test_agent_registry.py tests/test_agent_content_reliability.py tests/test_external_processing.py tests/test_source_aware_planning_acceptance.py
git commit -m "test: cover source-aware planning workflow"
```

## Plan Self-Review

- Spec coverage: Tasks 1–4 implement local source resolution and all four specialists; Tasks 5–6 implement both existing-agent extensions; Task 7 validates all acceptance criteria.
- Placeholder scan: no TODO/TBD markers or deferred implementation steps remain.
- Type consistency: `SourceSelection` is defined before all request references; `ResolvedSourceEvidence` is the only resolver result; each specialist output is added to the scenario union before chain tests consume it.

## Execution Handoff

The user previously selected **Subagent-Driven** execution. Dispatch one fresh implementation agent per task, run review gates after each task, and keep only one task in progress at a time where shared schemas or registry changes create dependencies.
