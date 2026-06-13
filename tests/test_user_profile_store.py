from pathlib import Path

import pytest

from app.schemas.user_profile import FormatPreference
from app.services.staff.user_profile_store import UserProfileStore


def test_get_returns_none_when_nothing_stored(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    assert store.get("capt-bench") is None


def test_upsert_stores_and_retrieves_profile(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    saved = store.upsert(
        "capt-bench",
        billet="SuppO",
        unit="3rd Bn 14th Marines",
        mos="0402",
        format_preference=FormatPreference.naval_letter,
        one_number_one_rule=True,
        style_notes="Naval letter only.",
    )
    retrieved = store.get("capt-bench")

    assert saved.billet == "SuppO"
    assert saved.unit == "3rd Bn 14th Marines"
    assert saved.mos == "0402"
    assert saved.one_number_one_rule is True
    assert retrieved is not None
    assert retrieved.billet == saved.billet


def test_upsert_strips_whitespace(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    saved = store.upsert("capt-bench", billet="  S-3  ", unit=" 1st Bn  ")

    assert saved.billet == "S-3"
    assert saved.unit == "1st Bn"


def test_upsert_raises_value_error_for_invalid_user_key(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    with pytest.raises(ValueError):
        store.upsert("/bad-key", billet="S-3")


def test_delete_removes_stored_profile(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path / "user-profiles")

    store.upsert("capt-bench", billet="XO")
    assert store.get("capt-bench") is not None

    store.delete("capt-bench")
    assert store.get("capt-bench") is None
