from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.bench_sections import BenchSectionsConfig
from app.services.session.handoff_store import is_valid_user_key


class BenchSectionsStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> BenchSectionsConfig | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return BenchSectionsConfig.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(self, user_key: str, sections: list[str]) -> BenchSectionsConfig:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        deduped = _dedupe_sections(sections)
        if not deduped:
            raise ValueError("sections list must contain at least one entry after deduplication.")
        config = BenchSectionsConfig(
            user_key=user_key,
            sections=deduped,
            updated_at=datetime.now(UTC),
        )
        self._path(user_key).write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return config

    def delete(self, user_key: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        path = self._path(user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"


def _dedupe_sections(sections: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for section in sections:
        cleaned = section.strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result
