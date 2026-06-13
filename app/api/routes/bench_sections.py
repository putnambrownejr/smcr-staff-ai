from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.bench_sections import BenchSectionsConfig, BenchSectionsResponse, BenchSectionsUpsertRequest
from app.services.staff.bench_sections_store import BenchSectionsStore

router = APIRouter(prefix="/bench-sections", tags=["bench sections"], dependencies=[LocalApiKeyDependency])


def get_bench_sections_store() -> Iterator[BenchSectionsStore]:
    settings = get_settings()
    yield BenchSectionsStore(settings.bench_sections_storage_dir)


@router.get("/{user_key}", response_model=BenchSectionsConfig)
def get_bench_sections_config(
    user_key: str,
    store: Annotated[BenchSectionsStore, Depends(get_bench_sections_store)],
) -> BenchSectionsConfig:
    config = store.get(user_key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"No bench sections stored for {user_key}.")
    return config


@router.put("/{user_key}", response_model=BenchSectionsResponse)
def upsert_bench_sections_config(
    user_key: str,
    request: BenchSectionsUpsertRequest,
    store: Annotated[BenchSectionsStore, Depends(get_bench_sections_store)],
) -> BenchSectionsResponse:
    try:
        config = store.upsert(user_key, request.sections)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return BenchSectionsResponse(
        config=config,
        message="Saved local bench section dropdown configuration.",
    )


@router.delete("/{user_key}", status_code=204)
def delete_bench_sections_config(
    user_key: str,
    store: Annotated[BenchSectionsStore, Depends(get_bench_sections_store)],
) -> None:
    if not store.delete(user_key):
        raise HTTPException(status_code=404, detail=f"No bench sections stored for {user_key}.")
