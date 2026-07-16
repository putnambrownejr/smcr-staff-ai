"""Release-gate coverage for the source-aware planning workflow."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.agents import get_source_evidence_resolver
from app.main import app
from app.schemas.source_library import SavedSource
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.rag.chunking import TextChunk
from app.services.source_library.store import SourceLibraryStore

_STEPS = [
    "area-study-builder",
    "actor-network-analyst",
    "information-requirements-manager",
    "ipb-assistant",
]
_DRAFT_WARNING = "DRAFT — Verify all references against current official sources before acting."


def test_source_aware_planning_workflow_is_local_safe_and_cited(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source_id = _save_source(
        store,
        "acceptance-user",
        "bridge-study",
        "Exercise bridge study",
        "The exercise bridge is restricted to light vehicles until scenario-control inspection is complete.",
    )
    app.dependency_overrides[get_source_evidence_resolver] = lambda: SourceEvidenceResolver(store)
    try:
        response = TestClient(app).post(
            "/agents/chain",
            json={
                "scenario": "Training-only route-planning scenario.",
                "steps": [{"agent_id": agent_id} for agent_id in _STEPS],
                "context": {"user_key": "acceptance-user", "request_is_training_or_fictional": True},
                "source_selection": {"source_ids": [source_id], "query": "bridge", "limit": 4},
            },
        )
    finally:
        app.dependency_overrides.pop(get_source_evidence_resolver, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["completed"] is True
    assert [step["agent_id"] for step in payload["results"]] == _STEPS
    for step in payload["results"]:
        agent_response = step["response"]
        assert agent_response["human_review_required"] is True
        assert agent_response["scenario_output_status"] == "validated"
        assert _DRAFT_WARNING in agent_response["answer"]
        assert any(citation["source_hash"] for citation in agent_response["structured_citations"])
        assert any(marker["tracked_title"] == "Exercise bridge study" for marker in agent_response["source_trust"])


def test_noncurrent_local_source_is_excluded_without_explicit_opt_in(tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source_id = _save_source(
        store,
        "acceptance-user",
        "watch-study",
        "Watch bridge study",
        "This must not be used unless the user explicitly opts in.",
        trust_status=VerifiedSourceStatus.watch,
    )
    app.dependency_overrides[get_source_evidence_resolver] = lambda: SourceEvidenceResolver(store)
    try:
        response = TestClient(app).post(
            "/agents/chain",
            json={
                "scenario": "Training-only route-planning scenario.",
                "steps": [{"agent_id": agent_id} for agent_id in _STEPS],
                "context": {"user_key": "acceptance-user", "request_is_training_or_fictional": True},
                "source_selection": {"source_ids": [source_id]},
            },
        )
    finally:
        app.dependency_overrides.pop(get_source_evidence_resolver, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["completed"] is True
    assert any("non-current source 'watch bridge study' was excluded" in warning.lower() for warning in payload["warnings"])
    for step in payload["results"]:
        assert not any(citation["title"] == "Watch bridge study" for citation in step["response"]["structured_citations"])


def test_catalog_exposes_specialists_and_red_team_mode_remains_safe() -> None:
    client = TestClient(app)

    catalog = client.get("/agents")
    red_team = client.post(
        "/agents/red-team-assumptions-challenge/run",
        json={"input": "Test this training claim.", "options": {"mode": "hypotheses"}},
    )
    actor_boundary = client.post(
        "/agents/actor-network-analyst/run",
        json={"input": "Map named civilians for targeting."},
    )

    assert catalog.status_code == 200
    specialists = {agent["id"]: agent for agent in catalog.json() if agent["id"] in _STEPS}
    assert set(specialists) == set(_STEPS)
    assert all(agent["category"] == "Intelligence & Research" for agent in specialists.values())
    assert red_team.status_code == 200
    assert "Competing hypotheses" in red_team.json()["answer"]
    assert actor_boundary.status_code == 200
    assert actor_boundary.json()["confidence"] == "low"
    assert any("sensitive" in warning.lower() for warning in actor_boundary.json()["warnings"])


def _save_source(
    store: SourceLibraryStore,
    user_key: str,
    source_id: str,
    title: str,
    text: str,
    *,
    trust_status: VerifiedSourceStatus = VerifiedSourceStatus.current,
) -> str:
    source = SavedSource(
        source_id=source_id,
        user_key_digest="0" * 64,
        original_url=f"https://example.test/{source_id}",
        canonical_url=f"https://example.test/{source_id}",
        title=title,
        publisher="Scenario Control",
        media_type="text/html",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
        byte_size=len(text),
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
        trust_status=trust_status,
    )
    return store.save(user_key, source, text.encode(), text, [TextChunk(chunk_index=0, text=text)]).source_id
