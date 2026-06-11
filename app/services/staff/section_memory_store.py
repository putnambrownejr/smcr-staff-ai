from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.core.security import DEFAULT_WARNINGS
from app.schemas.section_memory import SectionMemoryEntry, SectionMemoryProfile, SectionMemoryProfileUpsertRequest
from app.services.session.handoff_store import is_valid_user_key


class SectionMemoryStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> SectionMemoryProfile | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return SectionMemoryProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(self, user_key: str, request: SectionMemoryProfileUpsertRequest) -> SectionMemoryProfile:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        profile = SectionMemoryProfile(
            user_key=user_key,
            entries=_dedupe_entries(request.entries),
            updated_at=datetime.now(UTC),
            warnings=sorted(
                {
                    *DEFAULT_WARNINGS,
                    "Section memory is local-only continuity context, not authoritative staff direction.",
                }
            ),
        )
        self._path(user_key).write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        return profile

    def delete(self, user_key: str) -> bool:
        path = self._path(user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"


def _dedupe_entries(entries: list[SectionMemoryEntry]) -> list[SectionMemoryEntry]:
    seen: set[tuple[str, str]] = set()
    result: list[SectionMemoryEntry] = []
    for entry in entries:
        key = (entry.section.strip().lower(), entry.title.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result
