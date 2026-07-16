# G-9 Civil Network / Nodal Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Deliver an event-scoped, evidence-bound civil-network dataset that G-9 and planning agents can use for safe nodal analysis of fictional or public real-world civil environments.

**Architecture:** Owner-scoped JSON storage holds event-specific networks and immutable snapshots. A typed API validates public organization and role-bound public-leader nodes, typed relationships, provenance, trust state, and sensitive-content boundaries. The G-9 planner and specialist agents consume snapshots read-only; a Bench+Files workspace creates/edits records and renders a derived map.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, vanilla JavaScript SPA, flat JSON stores, existing Source Library and \`SourceEvidenceResolver\`, pytest, Ruff, mypy.

## Global Constraints

- UNCLASSIFIED, public, local-training, or fictional content only.
- Networks are owner-scoped and event-scoped; no silent cross-event reuse.
- Nodes may be public organizations, services, forums, broad groups, or public role-holders. A public role-holder requires public role, organization, source/date, and event relevance.
- Do not store private contact data, private affiliations, home/location details, sensitive movements, individual influence scores, targets, vulnerabilities, collection tasking, tactical advice, exploit paths, or intent predictions.
- Relationships are only \`coordination\`, \`dependency\`, \`influence\`, \`information_flow\`, \`authority_approval\`, \`resource_support\`, or \`legitimacy_trust\`.
- Every node/relationship is \`sourced_observation\`, \`analytic_inference\`, or \`planning_hypothesis\`; observations require evidence.
- Current reviewed saved sources may support observations by default. Watch/stale sources require explicit opt-in and outputs retain warnings.
- Snapshots are immutable and are consumed read-only by G-9 and specialist agents.
- Every advisory answer retains \`DRAFT — Verify all references against current official sources before acting.\`
- Dashboard remains a discovery surface for agents; it may provide dataset editing and derived-map views, not an agent execution console.

---

## File structure

- \`app/schemas/civil_network.py\` — contracts for networks, nodes, evidence, relationships, snapshots, and requests.
- \`app/services/staff/civil_network_store.py\` — owner-scoped JSON CRUD and immutable snapshots.
- \`app/services/staff/civil_network_service.py\` — source-resolution, evidence validation, and safe snapshot conversion.
- \`app/api/routes/civil_networks.py\` — local API endpoints.
- \`app/core/config.py\`, \`app/main.py\` — storage configuration and router registration.
- \`app/schemas/staff.py\`, \`app/services/staff/g9_planner.py\` — read-only G-9 projection.
- \`app/services/agents/{actor_network_agent,area_study_agent,information_requirements_agent,ipb_agent,red_team_agent}.py\` — read-only agent handoffs.
- \`app/static/dashboard/index.html\`, \`app/static/dashboard/dashboard.js\` — Bench+Files editor and derived map.
- \`tests/test_civil_network_{store,service,routes,acceptance}.py\`, \`tests/test_g9_civil_network.py\`, \`tests/test_civil_network_agent_handoffs.py\`, \`tests/test_dashboard_civil_network.py\` — regression coverage.

### Task 1: Contracts, owner-scoped storage, and snapshots

**Files:**
- Create: \`app/schemas/civil_network.py\`
- Create: \`app/services/staff/civil_network_store.py\`
- Modify: \`app/core/config.py\`
- Test: \`tests/test_civil_network_store.py\`

**Interfaces:**
- Produces \`CivilNetwork\`, \`CivilNetworkNode\`, \`CivilNetworkRelationship\`, \`CivilNetworkEvidence\`, \`CivilNetworkSnapshot\`, and their enums.
- Produces \`CivilNetworkStore(storage_dir).create/get/save/list/delete/snapshot\`.

- [ ] **Step 1: Write failing contract/store tests**

\`\`\`python
def test_store_isolates_networks_by_owner_and_event(tmp_path: Path) -> None:
    store = CivilNetworkStore(str(tmp_path))
    saved = store.create("owner-a", CivilNetwork(title="Flood exercise", event_id="flood-26", purpose="G-9 coordination"))
    assert store.get("owner-a", saved.id).event_id == "flood-26"
    with pytest.raises(KeyError):
        store.get("owner-b", saved.id)

def test_public_role_holder_and_sourced_relationship_require_fields() -> None:
    with pytest.raises(ValidationError):
        CivilNetworkNode(kind="public_role_holder", display_name="Example official")
    with pytest.raises(ValidationError, match="evidence"):
        CivilNetworkRelationship(
            from_node_id="county", to_node_id="hospital", kind="coordination",
            evidence_kind="sourced_observation", description="Coordinates support.",
        )
\`\`\`

- [ ] **Step 2: Run test to verify failure**

Run: \`uv run pytest tests/test_civil_network_store.py -q\`

Expected: FAIL because contracts and storage do not exist.

- [ ] **Step 3: Implement minimal contracts and storage**

\`\`\`python
class CivilEvidenceKind(StrEnum):
    sourced_observation = "sourced_observation"
    analytic_inference = "analytic_inference"
    planning_hypothesis = "planning_hypothesis"

class CivilNetworkNodeKind(StrEnum):
    organization = "organization"
    service = "service"
    forum = "forum"
    broad_group = "broad_group"
    public_role_holder = "public_role_holder"

class CivilNetworkStore:
    def snapshot(self, user_key: str, network_id: str, label: str) -> CivilNetworkSnapshot:
        network = self.get(user_key, network_id)
        snapshot = CivilNetworkSnapshot(label=label, network=network.model_copy(deep=True))
        network.snapshots.append(snapshot)
        self.save(user_key, network)
        return snapshot
\`\`\`

Use the SHA-256 owner-file pattern from \`SourceLibraryStore\`. Add \`default_civil_network_storage_dir()\` under local context, a Settings field, and include it in \`configured_storage_dirs\`. Enforce relationship references to existing nodes; sourced observations must have evidence; public role-holders must have role, organization, event relevance, source/date evidence; snapshots store deep-copied records.

- [ ] **Step 4: Run focused validation**

Run: \`uv run pytest tests/test_civil_network_store.py -q; uv run ruff check app/schemas/civil_network.py app/services/staff/civil_network_store.py tests/test_civil_network_store.py; uv run mypy app/schemas/civil_network.py app/services/staff/civil_network_store.py tests/test_civil_network_store.py\`

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

\`\`\`powershell
git add app/schemas/civil_network.py app/services/staff/civil_network_store.py app/core/config.py tests/test_civil_network_store.py
git commit -m "feat: add event-scoped civil network store"
\`\`\`

### Task 2: Evidence/trust service and API lifecycle

**Files:**
- Create: \`app/services/staff/civil_network_service.py\`
- Create: \`app/api/routes/civil_networks.py\`
- Modify: \`app/main.py\`
- Test: \`tests/test_civil_network_service.py\`
- Test: \`tests/test_civil_network_routes.py\`

**Interfaces:**
- \`CivilNetworkService(store, source_evidence_resolver).create_or_update(user_key, network, source_selection, include_noncurrent)\`.
- Routes: \`POST/GET/PUT/DELETE /civil-networks\`, \`POST /civil-networks/{id}/snapshots\`, \`GET /civil-networks/{id}/snapshots/{snapshot_id}\`.

- [ ] **Step 1: Write failing evidence and HTTP tests**

\`\`\`python
def test_current_selected_source_becomes_provenance(tmp_path: Path) -> None:
    service = service_with_saved_source(tmp_path, trust_status="current")
    saved = service.create_or_update("u", network_with_source_selection(), selection_for_saved_source(), False)
    assert saved.nodes[0].evidence[0].source_hash == "source-hash"
    assert saved.nodes[0].evidence[0].trust_status == "current"

def test_watch_source_requires_explicit_opt_in(tmp_path: Path) -> None:
    service = service_with_saved_source(tmp_path, trust_status="watch")
    with pytest.raises(ValueError, match="noncurrent"):
        service.create_or_update("u", network_with_source_selection(), selection_for_saved_source(), False)

def test_route_snapshot_is_owner_scoped(client: TestClient) -> None:
    created = client.post("/civil-networks", json={"user_key": "a", "network": valid_network_payload()})
    network_id = created.json()["id"]
    assert client.post(f"/civil-networks/{network_id}/snapshots", json={"user_key": "a", "label": "MSEL v1"}).status_code == 200
    assert client.get(f"/civil-networks/{network_id}", params={"user_key": "b"}).status_code == 404
\`\`\`

- [ ] **Step 2: Run tests to verify failure**

Run: \`uv run pytest tests/test_civil_network_service.py tests/test_civil_network_routes.py -q\`

Expected: FAIL because service/routes do not exist.

- [ ] **Step 3: Implement source normalization, safety, and routes**

\`\`\`python
def _require_observation_evidence(record: CivilNetworkNode | CivilNetworkRelationship) -> None:
    if record.evidence_kind is CivilEvidenceKind.sourced_observation and not record.evidence:
        raise ValueError("Sourced observations require at least one cited evidence record.")

@router.post("/civil-networks/{network_id}/snapshots", response_model=CivilNetworkSnapshot)
def snapshot_civil_network(network_id: str, request: CivilNetworkSnapshotRequest,
                           service: Annotated[CivilNetworkService, Depends(get_civil_network_service)]) -> CivilNetworkSnapshot:
    return service.snapshot(request.user_key, network_id, request.label)
\`\`\`

Resolve selections only with the existing \`SourceEvidenceResolver\`; never fetch URLs. Retain source id/hash/title/URL/publisher/retrieval date/trust state/excerpt. Require manual citations to have title, retrieval date, URL or bibliographic note, excerpt, confidence, and reviewer state. Run \`detect_sensitive_input\` over all editable text, map cross-owner misses to 404 and validation/trust failures to 422. Do not infer a relationship merely because nodes co-occur in a source.

- [ ] **Step 4: Run focused validation**

Run: \`uv run pytest tests/test_civil_network_store.py tests/test_civil_network_service.py tests/test_civil_network_routes.py tests/test_source_library.py -q; uv run ruff check app/services/staff/civil_network_service.py app/api/routes/civil_networks.py tests/test_civil_network_service.py tests/test_civil_network_routes.py; uv run mypy app/services/staff/civil_network_service.py app/api/routes/civil_networks.py tests/test_civil_network_service.py tests/test_civil_network_routes.py\`

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

\`\`\`powershell
git add app/services/staff/civil_network_service.py app/api/routes/civil_networks.py app/main.py tests/test_civil_network_service.py tests/test_civil_network_routes.py
git commit -m "feat: expose civil network evidence API"
\`\`\`

### Task 3: G-9 and specialist-agent read-only snapshot handoffs

**Files:**
- Modify: \`app/schemas/staff.py\`
- Modify: \`app/services/staff/g9_planner.py\`
- Modify: \`app/services/agents/actor_network_agent.py\`
- Modify: \`app/services/agents/area_study_agent.py\`
- Modify: \`app/services/agents/information_requirements_agent.py\`
- Modify: \`app/services/agents/ipb_agent.py\`
- Modify: \`app/services/agents/red_team_agent.py\`
- Test: \`tests/test_g9_civil_network.py\`
- Test: \`tests/test_civil_network_agent_handoffs.py\`

**Interfaces:**
- \`G9PlanningRequest.civil_network_snapshot: CivilNetworkSnapshot | None\`.
- \`context.extra["civil_network_snapshot"]\` validates as \`CivilNetworkSnapshot\`; agents read it but never mutate it.
- \`G9PlanningResponse.civil_network_assessment: list[str]\`.

- [ ] **Step 1: Write failing handoff tests**

\`\`\`python
def test_g9_preserves_snapshot_evidence_labels() -> None:
    response = G9Planner().build(G9PlanningRequest(
        title="Flood", supported_problem="Coordinate support.", civil_network_snapshot=network_snapshot(),
    ))
    assert any("Sourced observation" in line for line in response.civil_network_assessment)
    assert any("Planning hypothesis" in line for line in response.civil_network_assessment)

def test_agents_keep_observations_and_hypotheses_distinct() -> None:
    for agent in (build_actor_network_agent(), build_ipb_agent(), build_red_team_agent()):
        response = agent.run("Assess the exercise.", context_with_snapshot())
        assert "Planning hypothesis" in response.answer
        assert "DRAFT — Verify all references against current official sources before acting." in response.answer
\`\`\`

- [ ] **Step 2: Run tests to verify failure**

Run: \`uv run pytest tests/test_g9_civil_network.py tests/test_civil_network_agent_handoffs.py -q\`

Expected: FAIL because no projection or handoff exists.

- [ ] **Step 3: Implement bounded projections**

\`\`\`python
def _civil_network_snapshot(context: AgentContext) -> CivilNetworkSnapshot | None:
    raw = context.extra.get("civil_network_snapshot")
    return CivilNetworkSnapshot.model_validate(raw) if isinstance(raw, dict) else None

def _civil_network_assessment(snapshot: CivilNetworkSnapshot | None) -> tuple[list[str], list[G9EvidenceAssessment], list[str]]:
    if snapshot is None:
        return ([], [], [])
    # Project existing labels/provenance only; do not infer or write relationships.
\`\`\`

G-9 projects organization/service dependencies into civil situation and partner coordination, and public role-holders into role-bound engagement considerations. Update Actor Network metadata so validated snapshot public role-holders are allowed, while named private civilians/targeting remain refused. Area Study, IR, IPB, and Red Team render observations, inferences, hypotheses, gaps, and stale-source warnings in separate sections and may ask high-level discriminators only—not collection-tasking instructions or operational recommendations.

- [ ] **Step 4: Run focused validation**

Run: \`uv run pytest tests/test_g9_planner.py tests/test_g9_civil_network.py tests/test_actor_network_agent.py tests/test_area_study_agent.py tests/test_information_requirements_agent.py tests/test_ipb_agent.py tests/test_red_team_modes.py tests/test_civil_network_agent_handoffs.py -q; uv run ruff check app/schemas/staff.py app/services/staff/g9_planner.py app/services/agents tests/test_g9_civil_network.py tests/test_civil_network_agent_handoffs.py; uv run mypy app/schemas/staff.py app/services/staff/g9_planner.py app/services/agents/actor_network_agent.py app/services/agents/area_study_agent.py app/services/agents/information_requirements_agent.py app/services/agents/ipb_agent.py app/services/agents/red_team_agent.py tests/test_g9_civil_network.py tests/test_civil_network_agent_handoffs.py\`

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

\`\`\`powershell
git add app/schemas/staff.py app/services/staff/g9_planner.py app/services/agents/actor_network_agent.py app/services/agents/area_study_agent.py app/services/agents/information_requirements_agent.py app/services/agents/ipb_agent.py app/services/agents/red_team_agent.py tests/test_g9_civil_network.py tests/test_civil_network_agent_handoffs.py
git commit -m "feat: use civil network snapshots in planning agents"
\`\`\`

### Task 4: Bench+Files data workspace, derived map, and acceptance

**Files:**
- Modify: \`app/static/dashboard/index.html\`
- Modify: \`app/static/dashboard/dashboard.js\`
- Modify: \`README.md\`
- Modify: \`docs/interagency_reference.md\`
- Test: \`tests/test_dashboard_civil_network.py\`
- Test: \`tests/test_civil_network_acceptance.py\`

**Interfaces:**
- A Bench+Files workspace creates/selects an event network, edits nodes/relationships/evidence, creates snapshots, and renders a derived map.
- UI uses civil-network API routes only; it never invokes an agent route.

- [ ] **Step 1: Write failing UI and acceptance tests**

\`\`\`python
def test_dashboard_has_data_first_civil_network_workspace() -> None:
    html = Path("app/static/dashboard/index.html").read_text(encoding="utf-8")
    script = Path("app/static/dashboard/dashboard.js").read_text(encoding="utf-8")
    assert 'id="civil-network-workspace"' in html
    assert "/civil-networks" in script
    assert "civilNetworkMap" in script
    assert "civil-network-agent-run" not in script

def test_snapshot_preserves_provenance_through_g9_and_agent_handoff(client: TestClient) -> None:
    snapshot = create_snapshot_with_current_source_and_manual_inference(client)
    g9 = client.post("/staff/g9-plan", json=g9_payload(snapshot)).json()
    assert any(item["source_label"] == "Reviewed emergency plan" for item in g9["evidence_and_assumptions"])
    assert "DRAFT — Verify all references against current official sources before acting." in g9["warnings"]
\`\`\`

- [ ] **Step 2: Run tests to verify failure**

Run: \`uv run pytest tests/test_dashboard_civil_network.py tests/test_civil_network_acceptance.py -q\`

Expected: FAIL because the workspace and end-to-end flow do not exist.

- [ ] **Step 3: Implement workspace and derived map**

\`\`\`javascript
function civilNetworkMap(network) {
  return network.relationships.map((edge) => ({
    from: edge.from_node_id,
    to: edge.to_node_id,
    label: edge.kind + " · " + edge.evidence_kind + " · " + edge.confidence,
    warning: edge.evidence.some((item) => item.trust_status !== "current"),
  }));
}
\`\`\`

Place the workspace under Bench+Files. Require event id/purpose; require public-role fields when that kind is selected; display evidence type, trust state, date, confidence, and reviewer state. Support filters for relationship type, evidence kind, confidence, review state, and warnings. Require confirmation before snapshot creation. Do not add centrality/vulnerability/influence scores, graph discovery, source fetching, or agent run buttons. Add concise README/interagency notes that the feature is event-scoped, public-source/citation-bound, advisory only, and unsuitable for private-person tracking, targeting, or authority determination.

- [ ] **Step 4: Run complete validation**

Run: \`uv run pytest tests/ -q; uv run mypy app tests; uv run ruff check .; git diff --check\`

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

\`\`\`powershell
git add app/static/dashboard/index.html app/static/dashboard/dashboard.js README.md docs/interagency_reference.md tests/test_dashboard_civil_network.py tests/test_civil_network_acceptance.py
git commit -m "feat: add civil network planning workspace"
\`\`\`

## Plan self-review

- Spec coverage: Task 1 implements typed event/owner isolation and snapshots. Task 2 implements local-source/manual-citation provenance, trust, safety, and API lifecycle. Task 3 implements read-only G-9 and specialist-agent use. Task 4 implements the required data-first workspace, map, end-to-end verification, and documentation.
- Placeholder scan: no incomplete or deferred requirements are present.
- Type consistency: Task 1 defines \`CivilNetworkSnapshot\`; Tasks 2–4 consume it. Only Tasks 1–2 mutate \`CivilNetwork\`; Task 3 projects it read-only.
