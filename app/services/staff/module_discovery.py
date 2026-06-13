"""
Discovers module packs from the repo-level modules/ directory.

A module pack is a sub-directory inside the configured modules root.
Each pack may contain an optional manifest.json and any number of
.md / .txt / .pdf files that can be ingested into local context.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.schemas.modules import ModuleFile, ModuleManifest, ModulePackDetail, ModulePackSummary

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
PROFILE_SEED_FILENAME = "smcr-profile.json"
CONTENT_TYPES: dict[str, str] = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
}


def _read_manifest(pack_dir: Path) -> ModuleManifest:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        return ModuleManifest(title=pack_dir.name.replace("-", " ").replace("_", " ").title())
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return ModuleManifest.model_validate(data)
    except Exception:  # noqa: BLE001
        logger.warning("Could not parse manifest.json in %s — using defaults.", pack_dir)
        return ModuleManifest(title=pack_dir.name)


def _pack_files(pack_dir: Path) -> list[ModuleFile]:
    files: list[ModuleFile] = []
    for path in sorted(pack_dir.iterdir()):
        if path.name == "manifest.json" or not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        files.append(
            ModuleFile(
                filename=path.name,
                size_bytes=path.stat().st_size,
                content_type=CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"),
            )
        )
    return files


class ModuleDiscovery:
    def __init__(self, modules_dir: str | Path) -> None:
        self._dir = Path(modules_dir)

    def _available(self) -> bool:
        return self._dir.exists() and self._dir.is_dir()

    def list_packs(self) -> list[ModulePackSummary]:
        if not self._available():
            return []
        summaries: list[ModulePackSummary] = []
        for candidate in sorted(self._dir.iterdir()):
            if not candidate.is_dir() or candidate.name.startswith("."):
                continue
            manifest = _read_manifest(candidate)
            files = _pack_files(candidate)
            summaries.append(
                ModulePackSummary(
                    pack_name=candidate.name,
                    manifest=manifest,
                    file_count=len(files),
                    supported_file_count=len(files),
                )
            )
        return summaries

    def get_pack(self, pack_name: str) -> ModulePackDetail | None:
        if not self._available():
            return None
        pack_dir = self._dir / pack_name
        if not pack_dir.exists() or not pack_dir.is_dir():
            return None
        manifest = _read_manifest(pack_dir)
        files = _pack_files(pack_dir)
        return ModulePackDetail(
            pack_name=pack_name,
            manifest=manifest,
            file_count=len(files),
            supported_file_count=len(files),
            files=files,
        )

    def pack_file_path(self, pack_name: str, filename: str) -> Path | None:
        """Return the absolute path to a file inside a pack, or None if invalid."""
        if not self._available():
            return None
        pack_dir = self._dir / pack_name
        if not pack_dir.is_dir():
            return None
        candidate = (pack_dir / filename).resolve()
        try:
            candidate.relative_to(pack_dir.resolve())
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        if candidate.name != PROFILE_SEED_FILENAME and candidate.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return None
        return candidate
