from pathlib import Path

import pytest

from app.schemas.cadences import CadenceCreateRequest, CadenceRating
from app.services.fitness.cadence_store import CadenceStore


def test_cadence_store_isolates_users_and_requires_adult_opt_in(tmp_path: Path) -> None:
    store = CadenceStore(tmp_path)
    created = store.create(
        CadenceCreateRequest(
            user_key="alpha",
            title="After Dark",
            text="A salty but non-targeted private cadence.",
            rating=CadenceRating.adult,
        )
    )

    assert created not in store.list_records("alpha")
    assert created in store.list_records("alpha", include_adult=True)
    assert created not in store.list_records("bravo", include_adult=True)
    assert store.delete("alpha", created.cadence_id) is True


def test_cadence_store_rejects_hazing_even_when_adult(tmp_path: Path) -> None:
    store = CadenceStore(tmp_path)
    with pytest.raises(ValueError, match="hazing"):
        store.create(
            CadenceCreateRequest(
                user_key="alpha",
                title="Bad",
                text="This is a hazing cadence.",
                rating=CadenceRating.adult,
            )
        )


def test_built_ins_cannot_be_deleted(tmp_path: Path) -> None:
    store = CadenceStore(tmp_path)
    assert store.list_records("alpha")
    assert store.delete("alpha", "builtin-set-the-pace") is False
