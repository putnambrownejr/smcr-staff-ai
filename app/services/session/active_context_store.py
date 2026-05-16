from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.core.security import DEFAULT_WARNINGS
from app.schemas.user_context import ActiveUserContext


class ActiveUserContextStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def upsert(self, context: ActiveUserContext) -> ActiveUserContext:
        context.updated_at = datetime.now(UTC)
        context.warnings = sorted(
            set(
                [
                    *context.warnings,
                    *DEFAULT_WARNINGS,
                    "This active context is a temporary local bias layer, not authoritative unit data.",
                ]
            )
        )
        self._path(context.user_key).write_text(context.model_dump_json(indent=2), encoding="utf-8")
        return context

    def get(self, user_key: str) -> ActiveUserContext | None:
        path = self._path(user_key)
        if not path.exists():
            return None
        context = ActiveUserContext.model_validate_json(path.read_text(encoding="utf-8"))
        if context.expires_at is not None and context.expires_at < datetime.now(UTC):
            return None
        return context

    def delete(self, user_key: str) -> bool:
        path = self._path(user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode()).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"
