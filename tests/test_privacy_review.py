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


def test_privacy_sweep_preserves_unstaged_status_and_full_filename(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    file_path = repo_root / "example.md"
    file_path.write_text("Public example.\n", encoding="utf-8")
    subprocess.run(["git", "add", "example.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "Initial example"], cwd=repo_root, check=True, capture_output=True)
    file_path.write_text("Revised public example.\n", encoding="utf-8")

    response = RepoPrivacySweeper(repo_root).sweep()

    assert "example.md" in response.unstaged_files
    assert "example.md" not in response.staged_files


def test_privacy_sweep_flags_pii_in_staged_diff(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    file_path = repo_root / "notes.md"
    file_path.write_text("phone: 555-123-4567\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.md"], cwd=repo_root, check=True)

    response = RepoPrivacySweeper(repo_root).sweep()

    assert response.safe_to_push is False
    assert any("PII" in finding.title for finding in response.findings)


def test_privacy_sweep_recognizes_ignored_directory_contents(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    (repo_root / ".gitignore").write_text("data/local_context/\nprojects/\n", encoding="utf-8")
    for folder in ("data/local_context/notes", "projects/example/notes"):
        directory = repo_root / folder
        directory.mkdir(parents=True)
        (directory / "example.md").write_text("Fictional example.\n", encoding="utf-8")

    response = RepoPrivacySweeper(repo_root).sweep()

    assert not any(finding.category == "ignore-rules" for finding in response.findings)


def test_privacy_sweep_flags_force_tracked_project_output(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    directory = repo_root / "projects" / "example"
    directory.mkdir(parents=True)
    (directory / "output.md").write_text("Fictional example.\n", encoding="utf-8")
    subprocess.run(["git", "add", "projects"], cwd=repo_root, check=True)

    response = RepoPrivacySweeper(repo_root).sweep()

    assert any("projects/example/output.md" in finding.affected_paths for finding in response.findings)


def test_privacy_sweep_only_exempts_empty_known_directory_markers(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    marker = repo_root / "data" / "local_context" / ".gitkeep"
    marker.parent.mkdir(parents=True)
    marker.write_text("\n", encoding="utf-8")
    subprocess.run(["git", "add", "data"], cwd=repo_root, check=True)
    response = RepoPrivacySweeper(repo_root).sweep()
    assert not any(finding.category == "tracked-paths" for finding in response.findings)

    marker.write_text("This is no longer an empty marker.\n", encoding="utf-8")
    subprocess.run(["git", "add", "data"], cwd=repo_root, check=True)
    response = RepoPrivacySweeper(repo_root).sweep()
    assert any(finding.category == "tracked-paths" for finding in response.findings)


def test_privacy_sweep_flags_binary_staged_marker_with_empty_working_copy(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    marker = repo_root / "data" / "local_context" / ".gitkeep"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"\xff")
    subprocess.run(["git", "add", "data"], cwd=repo_root, check=True)
    marker.write_text("\n", encoding="utf-8")

    response = RepoPrivacySweeper(repo_root).sweep()

    assert any(finding.category == "tracked-paths" for finding in response.findings)


def test_privacy_route_sweeps_server_repo_and_ignores_caller_path(tmp_path: Path) -> None:
    # The route must always sweep its own repo. A caller-supplied repo_root is
    # ignored (issue #19): the sweep cannot be redirected to an arbitrary path.
    client = TestClient(app)

    response = client.post(
        "/privacy/pre-push-review",
        json={"repo_root": str(tmp_path), "include_untracked": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["git_available"] is True
    # The reported root is the server's repo, never the caller-supplied tmp_path.
    assert str(tmp_path) not in payload["repo_root"]


def _init_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, check=True)
    return tmp_path
