from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.history import HistoryImportRequest, HistoryImportResponse
from app.services.history.local_history_store import LocalHistoryStore
from app.services.history.today_in_history import extract_history_items_from_markdown

router = APIRouter(prefix="/history", tags=["history"], dependencies=[LocalApiKeyDependency])


def get_history_store() -> LocalHistoryStore:
    settings = get_settings()
    return LocalHistoryStore(settings.history_storage_dir)


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
