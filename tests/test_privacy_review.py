import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.privacy.repo_privacy_sweeper import RepoPrivacySweeper


def test_privacy_sweep_flags_tracked_local_only_note(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    note_path = repo_root / "docs" / "offline_notes.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("Personal drill note.\n", encoding="utf-8")
    subprocess.run(["git", "add", "docs/offline_notes.md"], cwd=repo_root, check=True)

    response = RepoPrivacySweeper(repo_root).sweep()

    assert response.safe_to_push is False
    assert any("Tracked local-only" in finding.title for finding in response.findings)
    assert "docs/offline_notes.md" in response.staged_files


def test_privacy_sweep_flags_pii_in_staged_diff(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    file_path = repo_root / "notes.md"
    file_path.write_text("phone: 555-123-4567\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.md"], cwd=repo_root, check=True)

    response = RepoPrivacySweeper(repo_root).sweep()

    assert response.safe_to_push is False
    assert any("PII" in finding.title for finding in response.findings)


def test_privacy_route_returns_clean_result_for_empty_repo(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    client = TestClient(app)

    response = client.post("/privacy/pre-push-review", json={"repo_root": str(repo_root)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["git_available"] is True
    assert payload["safe_to_push"] is True


def _init_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, check=True)
    return tmp_path
