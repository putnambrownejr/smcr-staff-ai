import hashlib
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import app.api.routes.training as training_routes
from app.main import app
from app.schemas.source_library import SavedSource
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.rag.chunking import TextChunk
from app.services.source_library.store import SourceLibraryStore


def test_training_scenario_accepts_confirmed_fictional_strategic_lens() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            **_scenario_payload(),
            "strategic_lens": {
                "mode": "fictional",
                "actor_name": "Aster Guard",
                "fictional_actor_confirmed": True,
                "posture_cards": ["indirect_leverage", "information_contest"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["strategic_lens"]["actor_name"] == "Aster Guard"
    assert payload["adversary_profile"][0]["name"] == "Aster Guard"
    assert any("Aster Guard" in line for line in payload["redcell_questions"])
    assert any("scenario assumption" in line.lower() for line in payload["facilitator_notes"])


def test_public_lens_requires_selected_local_sources() -> None:
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            **_scenario_payload(),
            "source_items": [{"title": "Free-form", "excerpt": "Must not be accepted."}],
            "strategic_lens": {"mode": "public_source", "actor_name": "Example force"},
        },
    )

    assert response.status_code == 422
    assert "reviewed local evidence" in response.json()["detail"].lower()


def test_public_lens_uses_owner_scoped_current_local_source(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source_id = _save_source(store, "owner", "current", VerifiedSourceStatus.current)
    monkeypatch.setattr(
        training_routes,
        "get_training_source_evidence_resolver",
        lambda: SourceEvidenceResolver(store),
    )
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            **_scenario_payload(),
            "user_key": "owner",
            "source_selection": {"source_ids": [source_id]},
            "strategic_lens": {"mode": "public_source", "actor_name": "Example force"},
        },
    )

    assert response.status_code == 200
    lens = response.json()["strategic_lens"]
    assert lens["evidence_observations"]
    assert lens["evidence_provenance"][0]["trust_status"] == "current"
    assert any("not a forecast" in note.lower() for note in response.json()["facilitator_notes"])


def test_public_lens_excludes_watch_source_without_opt_in(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    store = SourceLibraryStore(tmp_path)
    source_id = _save_source(store, "owner", "watch", VerifiedSourceStatus.watch)
    monkeypatch.setattr(
        training_routes,
        "get_training_source_evidence_resolver",
        lambda: SourceEvidenceResolver(store),
    )
    client = TestClient(app)

    response = client.post(
        "/training/scenario",
        json={
            **_scenario_payload(),
            "user_key": "owner",
            "source_selection": {"source_ids": [source_id]},
            "strategic_lens": {"mode": "public_source", "actor_name": "Example force"},
        },
    )

    assert response.status_code == 422
    assert "reviewed local evidence" in response.json()["detail"].lower()


def _scenario_payload() -> dict[str, object]:
    return {
        "scenario_type": "staff_drill",
        "title": "Strategic lens drill",
        "training_objective": "Practice decision-making and product flow.",
    }


def _save_source(
    store: SourceLibraryStore,
    user_key: str,
    source_id: str,
    trust_status: VerifiedSourceStatus,
) -> str:
    text = "A reviewed public observation establishes an exercise planning condition."
    source = SavedSource(
        source_id=source_id,
        user_key_digest="0" * 64,
        original_url=f"https://example.test/{source_id}",
        canonical_url=f"https://example.test/{source_id}",
        title="Reviewed source",
        publisher="Example publisher",
        media_type="text/plain",
        content_hash=hashlib.sha256(source_id.encode()).hexdigest(),
        byte_size=len(text),
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
        trust_status=trust_status,
    )
    return store.save(
        user_key,
        source,
        text.encode(),
        text,
        [TextChunk(chunk_index=0, text=text)],
    ).source_id
