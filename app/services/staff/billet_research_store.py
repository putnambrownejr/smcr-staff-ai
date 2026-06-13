from __future__ import annotations

import hashlib
from pathlib import Path

from app.services.session.handoff_store import is_valid_user_key


class BilletResearchStore:
    def __init__(self, storage_dir: str) -> None:
        self._dir = Path(storage_dir)

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode()).hexdigest()[:24]
        return self._dir / f"{digest}.md"

    def get(self, user_key: str) -> str | None:
        path = self._path(user_key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def upsert(self, user_key: str, content: str) -> str:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path(user_key).write_text(content, encoding="utf-8")
        return content

    def delete(self, user_key: str) -> None:
        path = self._path(user_key)
        if path.exists():
            path.unlink()
