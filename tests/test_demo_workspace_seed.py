"""Tests for the demo-mode baseline workspace seed (POST /demo/workspace/seed)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest
from app.services.actions.tracker import ActionTracker
from app.services.demo.scenarios import DEMO_USER_KEY
from app.services.user_docs.store import UserDocsStore


@pytest.fixture()
def seeded_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    dirs = {
        "user_docs": tmp_path / "User Docs",
        "projects": tmp_path / "projects",
        "actions": tmp_path / "actions",
    }
    settings = get_settings()
    monkeypatch.setattr(settings, "user_docs_dir", str(dirs["user_docs"]))
    monkeypatch.setattr(settings, "projects_dir", str(dirs["projects"]))
    monkeypatch.setattr(settings, "actions_storage_dir", str(dirs["actions"]))
    return dirs


def test_seed_creates_baseline_demo_files(seeded_dirs: dict[str, Path]) -> None:
    client = TestClient(app)

    response = client.post("/demo/workspace/seed")

    assert response.status_code == 200
    body = response.json()
    assert body["user_key"] == DEMO_USER_KEY
    assert body["seeded"] == {"notebook": 3, "fitreps": 2, "generations": 2, "actions": 3}

    store = UserDocsStore(seeded_dirs["user_docs"], seeded_dirs["projects"])
    notes = store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)
    fitreps = store.list_category(UserDocCategory.fitreps, DEMO_USER_KEY)
    generations = store.list_category(UserDocCategory.generations, DEMO_USER_KEY)
    assert len(notes) == 3
    assert len(fitreps) == 2
    assert len(generations) == 2

    # FitReps carry the full slider payload the dashboard round-trips.
    scores = fitreps[0].fields["scores"]
    assert set(scores) == {"mission", "individual", "leadership", "intellect", "fitness"}

    # Generations persist a path matching their real id, so Open location
    # resolves to the actual file (see _resolve_reveal_target).
    for entry in generations:
        assert entry.fields["path"] == f"User Docs/Generations/{entry.id}.md"

    tracker = ActionTracker(seeded_dirs["actions"])
    demo_actions = [r for r in tracker.list(user_key=DEMO_USER_KEY, include_closed=True) if r.user_key == DEMO_USER_KEY]
    assert len(demo_actions) == 3


def test_seed_resets_to_the_same_baseline(seeded_dirs: dict[str, Path]) -> None:
    client = TestClient(app)
    client.post("/demo/workspace/seed")

    # Simulate a demo session leaving extra state behind.
    store = UserDocsStore(seeded_dirs["user_docs"], seeded_dirs["projects"])
    store.create(UserDocCategory.notebook, DEMO_USER_KEY, UserDocCreateRequest(title="Scratch", body="left over"))
    assert len(store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)) == 4

    response = client.post("/demo/workspace/seed")

    assert response.status_code == 200
    assert len(store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)) == 3
    titles = {n.title for n in store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)}
    assert "Scratch" not in titles


def test_seed_only_if_empty_populates_a_fresh_demo_then_preserves_edits(
    seeded_dirs: dict[str, Path],
) -> None:
    client = TestClient(app)

    # First call on an empty demo workspace seeds the baseline.
    first = client.post("/demo/workspace/seed", params={"only_if_empty": "true"})
    assert first.status_code == 200
    assert first.json()["skipped"] is False
    assert first.json()["seeded"]["notebook"] == 3

    # A demo-session edit lands on the demo key.
    store = UserDocsStore(seeded_dirs["user_docs"], seeded_dirs["projects"])
    store.create(UserDocCategory.notebook, DEMO_USER_KEY, UserDocCreateRequest(title="Session edit", body="x"))
    assert len(store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)) == 4

    # A second only-if-empty call (a page refresh mid-demo) is a no-op, so the
    # edit survives.
    second = client.post("/demo/workspace/seed", params={"only_if_empty": "true"})
    assert second.status_code == 200
    assert second.json()["skipped"] is True
    assert second.json()["seeded"] is None
    assert len(store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)) == 4

    # An explicit toggle (default, full reset) wipes back to the baseline.
    third = client.post("/demo/workspace/seed")
    assert third.json()["skipped"] is False
    assert len(store.list_category(UserDocCategory.notebook, DEMO_USER_KEY)) == 3


def test_seed_leaves_other_users_data_alone(seeded_dirs: dict[str, Path]) -> None:
    client = TestClient(app)
    store = UserDocsStore(seeded_dirs["user_docs"], seeded_dirs["projects"])
    personal = store.create(
        UserDocCategory.notebook, "real-user-key", UserDocCreateRequest(title="Mine", body="personal note")
    )
    tracker = ActionTracker(seeded_dirs["actions"])
    from app.schemas.actions import ActionItemRequest

    keyless = tracker.track([ActionItemRequest(title="Keyless action")])[0]

    client.post("/demo/workspace/seed")
    client.post("/demo/workspace/seed")

    assert store.get(UserDocCategory.notebook, "real-user-key", personal.id) is not None
    remaining_ids = {r.action_id for r in tracker.list(include_closed=True)}
    assert keyless.action_id in remaining_ids
