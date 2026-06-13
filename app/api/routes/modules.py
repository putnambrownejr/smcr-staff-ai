from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.modules import ModuleIngestResult, ModulePackDetail, ModulePackSummary
from app.services.staff.module_discovery import ModuleDiscovery
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/modules", tags=["modules"], dependencies=[LocalApiKeyDependency])

MODULE_TAG = "module"


def get_discovery() -> ModuleDiscovery:
    settings = get_settings()
    return ModuleDiscovery(settings.module_packs_dir)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


@router.get("", response_model=list[ModulePackSummary])
def list_module_packs(
    discovery: Annotated[ModuleDiscovery, Depends(get_discovery)],
) -> list[ModulePackSummary]:
    return discovery.list_packs()


@router.get("/{pack_name}", response_model=ModulePackDetail)
def get_module_pack(
    pack_name: str,
    discovery: Annotated[ModuleDiscovery, Depends(get_discovery)],
) -> ModulePackDetail:
    detail = discovery.get_pack(pack_name)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Module pack '{pack_name}' not found.")
    return detail


@router.post("/{pack_name}/ingest", response_model=ModuleIngestResult)
def ingest_module_pack(
    pack_name: str,
    discovery: Annotated[ModuleDiscovery, Depends(get_discovery)],
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> ModuleIngestResult:
    detail = discovery.get_pack(pack_name)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Module pack '{pack_name}' not found.")

    # Remove any previously ingested files from this pack so re-ingest is idempotent.
    existing = [m for m in store.list() if MODULE_TAG in m.tags and pack_name in m.tags]
    replaced = 0
    for meta in existing:
        if store.delete(meta.context_id):
            replaced += 1

    ingested: list[str] = []
    skipped: list[str] = []

    for module_file in detail.files:
        file_path = discovery.pack_file_path(pack_name, module_file.filename)
        if file_path is None:
            skipped.append(module_file.filename)
            continue
        try:
            content = file_path.read_bytes()
            store.save(
                filename=module_file.filename,
                content=content,
                content_type=module_file.content_type,
                tags=[MODULE_TAG, pack_name],
                document_type="reference_note",
                consent_ack=True,
            )
            ingested.append(module_file.filename)
        except ValueError:
            skipped.append(module_file.filename)
        except Exception:  # noqa: BLE001
            skipped.append(module_file.filename)

    parts = [f"Ingested {len(ingested)} file(s) from '{pack_name}'."]
    if replaced:
        parts.append(f"Replaced {replaced} previous version(s).")
    if skipped:
        parts.append(f"Skipped {len(skipped)} file(s) (too large or unsupported).")

    return ModuleIngestResult(
        pack_name=pack_name,
        ingested=ingested,
        skipped=skipped,
        replaced=replaced,
        message=" ".join(parts),
    )
