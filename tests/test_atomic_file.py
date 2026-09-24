from pathlib import Path

import pytest

from app.services.storage.atomic_file import atomic_write_text


def test_failed_publish_keeps_previous_file_and_removes_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "record.json"
    path.write_text('{"version": 1}', encoding="utf-8")

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("simulated publish failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated publish failure"):
        atomic_write_text(path, '{"version": 2}')

    assert path.read_text(encoding="utf-8") == '{"version": 1}'
    assert list(tmp_path.glob("*.tmp")) == []
