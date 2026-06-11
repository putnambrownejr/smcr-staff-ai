import logging
import os
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from app.core.config import (
    Settings,
    configured_storage_dirs,
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


@pytest.mark.skipif(os.name != "nt", reason="Windows LOCALAPPDATA fallback is Windows-specific.")
def test_windows_default_local_state_root_uses_localappdata(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SMCR_STAFF_AI_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")

    root = default_local_state_root()

    assert root == Path(r"C:\Users\tester\AppData\Local") / "smcr-staff-ai"
    assert "data\\local_context" not in str(default_local_context_dir()).lower()
    assert default_database_url().endswith("/smcr-staff-ai/smcr_staff_ai.db")


def test_settings_default_paths_point_outside_repo_when_unset(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SMCR_STAFF_AI_HOME", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_CONTEXT_STORAGE_DIR", raising=False)
    monkeypatch.delenv("SESSION_HANDOFF_STORAGE_DIR", raising=False)

    settings = Settings(_env_file=None)
    normalized_context_dir = settings.local_context_storage_dir.replace("\\", "/")

    assert "data/local_context" not in normalized_context_dir.lower()
    assert normalized_context_dir.endswith("smcr-staff-ai/local_context")
    assert Path(settings.session_handoff_storage_dir) == Path(settings.local_context_storage_dir) / "session_handoffs"
    assert Path(settings.actions_storage_dir) == Path(settings.local_context_storage_dir) / "actions"
    assert Path(settings.document_updates_storage_dir) == Path(settings.local_context_storage_dir) / "document_updates"
    assert Path(settings.drill_plans_storage_dir) == Path(settings.local_context_storage_dir) / "drill_plans"
    assert Path(settings.opportunities_storage_dir) == Path(settings.local_context_storage_dir) / "opportunities"
    assert Path(settings.source_states_storage_dir) == Path(settings.local_context_storage_dir) / "source_states"
    assert settings.database_url.endswith("/smcr-staff-ai/smcr_staff_ai.db")


def test_configured_storage_dirs_include_first_class_substores(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SMCR_STAFF_AI_HOME", str(tmp_path / "home"))
    settings = Settings(_env_file=None)

    storage_dirs = configured_storage_dirs(settings)

    assert Path(settings.active_user_context_storage_dir) in storage_dirs
    assert Path(settings.actions_storage_dir) in storage_dirs
    assert Path(settings.document_updates_storage_dir) in storage_dirs
    assert Path(settings.drill_plans_storage_dir) in storage_dirs
    assert Path(settings.opportunities_storage_dir) in storage_dirs
    assert Path(settings.source_states_storage_dir) in storage_dirs


def test_warns_when_local_api_key_unset(caplog: LogCaptureFixture) -> None:
    from app.main import _warn_if_auth_disabled

    settings = Settings(_env_file=None, local_api_key=None)
    with caplog.at_level(logging.WARNING, logger="smcr_staff_ai"):
        _warn_if_auth_disabled(settings)

    assert any("LOCAL_API_KEY is not set" in record.message for record in caplog.records)


def test_no_warning_when_local_api_key_set(caplog: LogCaptureFixture) -> None:
    from app.main import _warn_if_auth_disabled

    settings = Settings(_env_file=None, local_api_key="set-key")
    with caplog.at_level(logging.WARNING, logger="smcr_staff_ai"):
        _warn_if_auth_disabled(settings)

    assert not any("LOCAL_API_KEY is not set" in record.message for record in caplog.records)
