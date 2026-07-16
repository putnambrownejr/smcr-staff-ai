# Strategic Lens and Fictional Adversary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe fictional posture cards and evidence-bound public-source strategic lenses to scenario construction, Red Team, Actor Network, and IPB.

**Architecture:** A shared `app.schemas.strategic_lens` contract and `StrategicLensBuilder` produce a normalized, non-tactical lens. Training routes resolve selected local sources through the existing `SourceEvidenceResolver` and pass evidence into the scenario engine. Agent options carry the same lens object into Red Team, Actor Network, and IPB; each agent uses it only for hypotheses, questions, and high-level exercise friction.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, existing Source Library and `SourceEvidenceResolver`, pytest, Ruff, mypy.

## Global Constraints

- UNCLASSIFIED, public, local, training, or fictional content only.
- Dashboard remains a discovery surface; do not add an agent execution console.
- No external fetch occurs during scenario or agent execution.
- Fictional mode requires a fictional actor and two to four posture cards.
- Public-source mode requires reviewed local evidence and keeps source hash, retrieval date, citation, and trust state.
- Public-source output must separate observations, hypotheses, gaps, competing interpretation, and discriminator.
- Do not create national/cultural stereotypes, intent predictions, targeting, collection tasking, tactical employment advice, exploit paths, sensitive movement analysis, or COMSEC guidance.
- Every advisory answer retains `DRAFT — Verify all references against current official sources before acting.`

---

### Task 1: Shared strategic-lens schema and pattern-card builder

**Files:**
- Create: `app/schemas/strategic_lens.py`
- Create: `app/services/training/strategic_lens.py`
- Test: `tests/test_strategic_lens.py`

**Interfaces:**
- Produces `StrategicLensMode`, `StrategicPostureCard`, `StrategicLensRequest`, and `StrategicLensOutput`.
- Produces `StrategicLensBuilder.build(request: StrategicLensRequest, evidence: list[dict[str, str]]) -> StrategicLensOutput`.

- [ ] **Step 1: Write failing contract tests**

```python
def test_fictional_lens_requires_two_to_four_distinct_cards() -> None:
    with pytest.raises(ValueError, match="two to four"):
        builder.build(StrategicLensRequest(mode="fictional", actor_name="Aster Guard", posture_cards=["indirect_leverage"]), [])

def test_public_source_lens_requires_resolved_evidence() -> None:
    with pytest.raises(ValueError, match="reviewed local evidence"):
        builder.build(StrategicLensRequest(mode="public_source", actor_name="Example force"), [])
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest tests/test_strategic_lens.py -q`

Expected: import failure for `StrategicLensRequest` and `StrategicLensBuilder`.

- [ ] **Step 3: Implement the contract and builder**

```python
class StrategicLensMode(StrEnum):
    fictional = "fictional"
    public_source = "public_source"

class StrategicPostureCard(StrEnum):
    indirect_leverage = "indirect_leverage"
    legitimacy_first = "legitimacy_first"
    threshold_sensitive = "threshold_sensitive"
    systems_friction = "systems_friction"
    information_contest = "information_contest"
    partner_reliance = "partner_reliance"
    short_term_risk = "short_term_risk"
    force_preservation = "force_preservation"
    asymmetric_systems_effect = "asymmetric_systems_effect"

class StrategicLensRequest(BaseModel):
    mode: StrategicLensMode
    actor_name: str = Field(min_length=1, max_length=160)
    posture_cards: list[StrategicPostureCard] = Field(default_factory=list)

class StrategicLensOutput(BaseModel):
    mode: StrategicLensMode
    actor_name: str
    strategic_objective: list[str] = Field(default_factory=list)
    theory_of_advantage: list[str] = Field(default_factory=list)
    risk_and_escalation_posture: list[str] = Field(default_factory=list)
    force_employment_preference: list[str] = Field(default_factory=list)
    information_posture: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    observable_indicators: list[str] = Field(default_factory=list)
    competing_interpretation: str = ""
    discriminator: str = ""
    evidence_observations: list[str] = Field(default_factory=list)
    source_hashes: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
```

Define each posture card as neutral planning language, high-level exercise friction, counter-pressure, and a question testing whether it applies. Do not include tactics, targets, vulnerabilities, nation names, or cultural generalizations. In fictional mode label all output as scenario assumptions. In public-source mode copy only attributed evidence excerpts into `evidence_observations`; derive no fact beyond those excerpts and label all framework statements as hypotheses.

- [ ] **Step 4: Add safety and provenance tests**

```python
def test_public_lens_preserves_local_source_provenance() -> None:
    lens = builder.build(public_request, [source_item])
    assert "bridge-hash" in lens.source_hashes
    assert lens.evidence_observations
    assert lens.competing_interpretation
    assert lens.discriminator
```

- [ ] **Step 5: Run focused validation**

Run: `uv run pytest tests/test_strategic_lens.py -q; uv run ruff check app/schemas/strategic_lens.py app/services/training/strategic_lens.py tests/test_strategic_lens.py; uv run mypy app/schemas/strategic_lens.py app/services/training/strategic_lens.py tests/test_strategic_lens.py`

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

```powershell
git add app/schemas/strategic_lens.py app/services/training/strategic_lens.py tests/test_strategic_lens.py
git commit -m "feat: add strategic lens pattern cards"
```

### Task 2: Source-aware Scenario Builder integration

**Files:**
- Modify: `app/schemas/training.py`
- Modify: `app/api/routes/training.py`
- Modify: `app/services/training/scenario_builder.py`
- Modify: `app/services/training/scenario_engine.py`
- Test: `tests/test_training_workflows.py`
- Test: `tests/test_training_strategic_lens.py`

**Interfaces:**
- `TrainingScenarioRequest` accepts `user_key: str | None`, `source_selection: SourceSelection | None`, and `strategic_lens: StrategicLensRequest | None`.
- `TrainingScenarioResponse` exposes `strategic_lens: StrategicLensOutput | None`.
- `build_s3_scenario_design(..., strategic_lens: StrategicLensOutput | None)` adds lens-aware profile, friction, and Red Cell questions.

- [ ] **Step 1: Write failing HTTP tests**

```python
def test_training_scenario_accepts_fictional_strategic_lens(client: TestClient) -> None:
    response = client.post("/training/scenario", json={
        **scenario_payload(),
        "strategic_lens": {
            "mode": "fictional", "actor_name": "Aster Guard",
            "posture_cards": ["indirect_leverage", "information_contest"],
        },
    })
    assert response.status_code == 200
    assert response.json()["strategic_lens"]["actor_name"] == "Aster Guard"
    assert any("Aster Guard" in line for line in response.json()["redcell_questions"])
```

- [ ] **Step 2: Add local-source dependency and validation**

Create `get_training_source_evidence_resolver()` using `SourceLibraryStore(get_settings().source_library_storage_dir)`. If a training request supplies `source_selection`, require `user_key`, resolve local evidence, and convert `ResolvedSourceEvidence.items` to the existing scenario source-item shape. Public-source lens mode requires a `source_selection` and nonempty resolved evidence; it must not use the legacy free-form `source_items` field as evidence. Never invoke a fetcher.

- [ ] **Step 3: Wire the lens through scenario construction**

```python
scenario_design = build_s3_scenario_design(
    ..., source_items=resolved_source_items,
    strategic_lens=lens,
)
return TrainingScenarioResponse(..., strategic_lens=lens)
```

When a fictional lens exists, use its actor name only if it is fictional mode; preserve the existing fictional place and country generation. Add its high-level friction to setting/frame/beat/question text, not to targets or tactics. When a public-source lens exists, preserve the user-provided subject only as an attributed analytical subject and include the lens evidence gaps in facilitator notes.

- [ ] **Step 4: Add source-trust regression tests**

```python
def test_public_lens_excludes_watch_source_without_opt_in(tmp_path: Path) -> None:
    response = post_training_scenario_with_source(trust_status="watch")
    assert response.status_code == 422
    assert "reviewed local evidence" in response.json()["detail"].lower()
```

- [ ] **Step 5: Run validation**

Run: `uv run pytest tests/test_training_workflows.py tests/test_training_strategic_lens.py tests/test_source_library.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add app/schemas/training.py app/api/routes/training.py app/services/training/scenario_builder.py app/services/training/scenario_engine.py tests/test_training_workflows.py tests/test_training_strategic_lens.py
git commit -m "feat: add strategic lens to training scenarios"
```

### Task 3: Red Team strategic-lens option

**Files:**
- Modify: `app/services/agents/red_team_agent.py`
- Test: `tests/test_red_team_strategic_lens.py`

**Interfaces:**
- Consumes `context.extra["agent_options"]["strategic_lens"]` as a validated `StrategicLensRequest` plus resolved `source_evidence`.
- Uses `StrategicLensBuilder` before mode-specific Red Team rendering.

- [ ] **Step 1: Write failing mode integration tests**

```python
def test_red_team_hypotheses_compares_lens_with_competing_interpretation() -> None:
    response = agent.run(
        "Pressure-test the exercise concept.",
        AgentContext(extra={"agent_options": {"mode": "hypotheses", "strategic_lens": fictional_lens_payload()}}),
    )
    assert "Strategic lens" in response.answer
    assert "Competing interpretation" in response.answer
    assert "Aster Guard" in response.answer
```

- [ ] **Step 2: Implement bounded rendering**

```python
def _strategic_lens(context: AgentContext) -> StrategicLensOutput | None:
    raw = _agent_options(context).get("strategic_lens")
    if raw is None:
        return None
    request = StrategicLensRequest.model_validate(raw)
    return StrategicLensBuilder().build(request, _source_evidence(context))
```

In assumptions mode, add mirror-imaging questions. In evidence mode, distinguish lens observations from assumptions. In hypotheses mode, render the lens, competing interpretation, and discriminator. Let Pydantic validation reject malformed lens payloads as 422 through the existing route behavior. Do not alter behavior when no lens is supplied.

- [ ] **Step 3: Run validation**

Run: `uv run pytest tests/test_red_team_modes.py tests/test_red_team_strategic_lens.py -q; uv run ruff check app/services/agents/red_team_agent.py tests/test_red_team_strategic_lens.py; uv run mypy app/services/agents/red_team_agent.py tests/test_red_team_strategic_lens.py`

Expected: all commands exit 0.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/red_team_agent.py tests/test_red_team_strategic_lens.py
git commit -m "feat: apply strategic lenses in red team modes"
```

### Task 4: Actor Network and IPB strategic-lens context

**Files:**
- Modify: `app/services/agents/actor_network_agent.py`
- Modify: `app/services/agents/ipb_agent.py`
- Test: `tests/test_actor_network_strategic_lens.py`
- Test: `tests/test_ipb_strategic_lens.py`

**Interfaces:**
- Both agents consume the same validated `StrategicLensOutput` from `agent_options` and local evidence.
- Neither agent changes a lens into targeting, intent prediction, collection tasking, or factual assertion.

- [ ] **Step 1: Write failing boundary tests**

```python
def test_actor_network_lens_remains_organization_level_hypothesis() -> None:
    response = actor.run("Map exercise actors.", context_with_fictional_lens())
    assert "planning hypothesis" in response.answer.lower()
    assert "individual" not in response.scenario_output["actors"][0]["actor"].lower()

def test_ipb_public_lens_separates_observation_and_hypothesis() -> None:
    response = ipb.run("Build exercise IPB.", context_with_public_lens_and_source())
    assert "Evidence" in response.answer and "Hypotheses" in response.answer
    assert "Competing interpretation" in response.answer
```

- [ ] **Step 2: Implement rendering and structured handoff additions**

Add `strategic_lens: dict[str, object] | None = None` to `ActorNetworkScenarioOutput` and `IpbScenarioOutput`. Store `lens.model_dump()` only after validation. Actor Network may add a generic organization-level hypothesis and gap; IPB may add high-level indicators/discriminators. Both answers must state that the lens is not a forecast of real-world conduct.

- [ ] **Step 3: Run validation**

Run: `uv run pytest tests/test_actor_network_agent.py tests/test_ipb_agent.py tests/test_actor_network_strategic_lens.py tests/test_ipb_strategic_lens.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add app/services/agents/actor_network_agent.py app/services/agents/ipb_agent.py app/schemas/scenario_handoff.py tests/test_actor_network_strategic_lens.py tests/test_ipb_strategic_lens.py
git commit -m "feat: carry strategic lenses into actor and IPB analysis"
```

### Task 5: Safety acceptance and release gate

**Files:**
- Create: `tests/test_strategic_lens_acceptance.py`
- Modify: `tests/test_agent_content_reliability.py`

**Interfaces:**
- Locks fictional/public-source separation, source-trust gates, non-tactical behavior, and all integration points.

- [ ] **Step 1: Add end-to-end acceptance coverage**

```python
def test_public_source_lens_is_cited_nonpredictive_and_local_only(client: TestClient, tmp_path: Path) -> None:
    response = post_public_lens_scenario(client, tmp_path)
    assert response.status_code == 200
    lens = response.json()["strategic_lens"]
    assert lens["evidence_observations"]
    assert lens["competing_interpretation"]
    assert lens["discriminator"]
    assert "target" not in " ".join(lens["theory_of_advantage"]).lower()
```

- [ ] **Step 2: Add rejection checks**

```python
@pytest.mark.parametrize("payload", [
    {"mode": "fictional", "actor_name": "Example", "posture_cards": ["indirect_leverage"]},
    {"mode": "public_source", "actor_name": "Example", "posture_cards": []},
])
def test_invalid_lens_requests_are_rejected(payload: dict[str, object]) -> None:
    assert post_scenario(payload).status_code == 422
```

- [ ] **Step 3: Run release validation**

Run:

```powershell
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit**

```powershell
git add tests/test_strategic_lens_acceptance.py tests/test_agent_content_reliability.py
git commit -m "test: cover strategic lens safety"
```

## Plan Self-Review

- Spec coverage: Task 1 creates both lens modes and cards; Task 2 integrates Scenario Builder and local evidence; Tasks 3–4 integrate all named agents; Task 5 enforces mode separation and safety constraints.
- Placeholder scan: no TODO/TBD markers or deferred implementation steps remain.
- Type consistency: `StrategicLensRequest` is the shared request type, `StrategicLensOutput` is the shared resolved type, and `StrategicLensBuilder.build()` is the only construction path.

## Execution Handoff

The project preference is **Subagent-Driven** execution: use one fresh subagent per task and review each deliverable before beginning dependent work.
