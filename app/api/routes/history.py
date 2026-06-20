from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import yaml
from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.history import (
    HistoryImportRequest,
    HistoryImportResponse,
    HistoryRefreshResponse,
    TodayInMarineHistoryItem,
)
from app.services.history.local_history_store import LocalHistoryStore
from app.services.history.today_in_history import extract_history_items_from_markdown
from app.services.history.wikipedia_history_service import WikipediaOnThisDayService

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SEED_PATH = _REPO_ROOT / "data" / "seed" / "usmc_history_on_this_day.example.yaml"

router = APIRouter(prefix="/history", tags=["history"], dependencies=[LocalApiKeyDependency])


def get_history_store() -> LocalHistoryStore:
    settings = get_settings()
    return LocalHistoryStore(settings.history_storage_dir)


def get_wikipedia_service() -> WikipediaOnThisDayService:
    return WikipediaOnThisDayService()


@router.post("/seed", response_model=HistoryRefreshResponse)
def seed_history_from_bundled_yaml(
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
) -> HistoryRefreshResponse:
    warnings: list[str] = []
    if not _SEED_PATH.exists():
        warnings.append(f"Seed file not found: {_SEED_PATH}")
        return HistoryRefreshResponse(
            fetched_count=0, imported_count=0,
            total_available=len(store.list_items()),
            date_checked="seed", warnings=warnings,
        )
    with open(_SEED_PATH, encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    items = [TodayInMarineHistoryItem.model_validate(item) for item in payload.get("items", [])]
    stored = store.merge(items)
    return HistoryRefreshResponse(
        fetched_count=len(items), imported_count=len(items),
        total_available=len(stored), date_checked="seed", warnings=warnings,
    )


@router.post("/refresh", response_model=HistoryRefreshResponse)
def refresh_history_for_today(
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
    service: Annotated[WikipediaOnThisDayService, Depends(get_wikipedia_service)],
) -> HistoryRefreshResponse:
    return service.refresh_for_date(datetime.now(UTC).date(), store)


@router.post("/import-markdown", response_model=HistoryImportResponse)
def import_history_markdown(
    request: HistoryImportRequest,
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
) -> HistoryImportResponse:
    imported_items = []
    warnings: list[str] = []
    for raw_path in request.markdown_paths:
        path = Path(raw_path)
        if not path.exists():
            warnings.append(f"Missing file: {path}")
            continue
        markdown = path.read_text(encoding="utf-8")
        extracted = extract_history_items_from_markdown(markdown, str(path))
        if not extracted:
            warnings.append(f"No dated history items found in: {path}")
            continue
        imported_items.extend(extracted)
    stored = store.replace(imported_items) if request.replace_existing else store.merge(imported_items)
    return HistoryImportResponse(
        imported_count=len(imported_items),
        total_available=len(stored),
        sources=request.markdown_paths,
        warnings=warnings,
    )
