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
from app.services.history.catalog import BUNDLED_HISTORY_PATHS
from app.services.history.local_history_store import LocalHistoryStore
from app.services.history.today_in_history import extract_history_items_from_markdown

router = APIRouter(prefix="/history", tags=["history"], dependencies=[LocalApiKeyDependency])


def get_history_store() -> LocalHistoryStore:
    settings = get_settings()
    return LocalHistoryStore(settings.history_storage_dir)


def _load_bundled_history() -> tuple[list[TodayInMarineHistoryItem], list[str]]:
    items: list[TodayInMarineHistoryItem] = []
    warnings: list[str] = []
    for path in BUNDLED_HISTORY_PATHS:
        if not path.exists():
            warnings.append(f"Seed file not found: {path}")
            continue
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        items.extend(
            TodayInMarineHistoryItem.model_validate(item)
            for item in payload.get("items", [])
        )
    return items, warnings


@router.post("/seed", response_model=HistoryRefreshResponse)
def seed_history_from_bundled_yaml(
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
) -> HistoryRefreshResponse:
    items, warnings = _load_bundled_history()
    if not items:
        return HistoryRefreshResponse(
            fetched_count=0, imported_count=0,
            total_available=len(store.list_items()),
            date_checked="seed", warnings=warnings,
        )
    stored = store.merge(items)
    return HistoryRefreshResponse(
        fetched_count=len(items), imported_count=len(items),
        total_available=len(stored), date_checked="seed", warnings=warnings,
    )


@router.post("/refresh", response_model=HistoryRefreshResponse)
def refresh_history_for_today(
    store: Annotated[LocalHistoryStore, Depends(get_history_store)],
) -> HistoryRefreshResponse:
    return HistoryRefreshResponse(
        fetched_count=0,
        imported_count=0,
        total_available=len(store.list_items()),
        date_checked=datetime.now(UTC).date().isoformat(),
        warnings=[
            "Automated Wikipedia history import is disabled because its events "
            "cannot be assigned a reliable U.S. service scope. Use cited bundled "
            "or explicitly scoped imported records."
        ],
    )


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
        extracted = extract_history_items_from_markdown(markdown, str(path), request.scope)
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
