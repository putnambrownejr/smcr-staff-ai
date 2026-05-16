from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from app.core.config import (
    Settings,
    default_database_url,
    default_local_context_dir,
    default_local_state_root,
    default_session_handoff_dir,
)


def test_default_local_state_root_prefers_explicit_home(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SMCR_STAFF_AI_HOME", str(tmp_path / "smcr-home"))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    root = default_local_state_root()

    assert root == tmp_path / "smcr-home"
    assert default_local_context_dir() == root / "local_context"
    assert default_session_handoff_dir() == root / "local_context" / "session_handoffs"


def test_windows_default_local_state_root_uses_localappdata(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SMCR_STAFF_AI_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")

    root = default_local_state_root()

    assert root == Path(r"C:\Users\tester\AppData\Local") / "smcr-staff-ai"
    assert "data\\local_context" not in str(default_local_context_dir()).lower()
    assert default_database_url().endswith("/smcr-staff-ai/smcr_staff_ai.db")


def test_settings_default_paths_point_outside_repo_when_unset(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SMCR_STAFF_AI_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_CONTEXT_STORAGE_DIR", raising=False)
    monkeypatch.delenv("SESSION_HANDOFF_STORAGE_DIR", raising=False)

    settings = Settings(_env_file=None)

    assert "data/local_context" not in settings.local_context_storage_dir.replace("\\", "/").lower()
    assert settings.local_context_storage_dir.endswith("smcr-staff-ai\\local_context")
    assert settings.session_handoff_storage_dir.endswith("smcr-staff-ai\\local_context\\session_handoffs")
    assert settings.database_url.endswith("/smcr-staff-ai/smcr_staff_ai.db")
