from pathlib import Path

import pytest

from app.services.staff.bench_sections_store import BenchSectionsStore


def test_get_returns_none_when_nothing_stored(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    assert store.get("capt-bench") is None


def test_upsert_stores_and_retrieves_sections(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    saved = store.upsert("capt-bench", ["S-1/Admin", "S-3"])
    retrieved = store.get("capt-bench")

    assert saved.sections == ["S-1/Admin", "S-3"]
    assert retrieved is not None
    assert retrieved.sections == ["S-1/Admin", "S-3"]


def test_upsert_deduplicates_and_strips_blank_entries(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    saved = store.upsert("capt-bench", [" S-1/Admin ", "", "s-1/admin", "  ", "S-6"])

    assert saved.sections == ["S-1/Admin", "S-6"]


def test_upsert_raises_value_error_for_invalid_user_key(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    with pytest.raises(ValueError):
        store.upsert("/", ["S-1/Admin"])


def test_upsert_raises_value_error_when_all_entries_blank_after_dedup(tmp_path: Path) -> None:
    store = BenchSectionsStore(tmp_path / "bench-sections")

    with pytest.raises(ValueError, match="at least one entry"):
        store.upsert("capt-bench", ["", "  ", "\t"])
