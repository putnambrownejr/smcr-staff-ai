from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from app.schemas.external_processing import (
    ExternalProcessingAuditEntry,
    ExternalProcessingAuditLog,
)

MAX_AUDIT_ENTRIES = 200


class ExternalProcessingAuditStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def append(self, user_key: str | None, entry: ExternalProcessingAuditEntry) -> ExternalProcessingAuditEntry:
        key = user_key or "local"
        normalized = entry.model_copy(update={"user_key_digest": self.user_key_digest(key)})
        log = self.get(key)
        log.entries.append(normalized)
        log.entries = log.entries[-MAX_AUDIT_ENTRIES:]
        self._path(key).write_text(log.model_dump_json(indent=2), encoding="utf-8")
        return normalized

    def get(self, user_key: str | None) -> ExternalProcessingAuditLog:
        key = user_key or "local"
        path = self._path(key)
        if not path.exists():
            return ExternalProcessingAuditLog()
        try:
            return ExternalProcessingAuditLog.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            backup = path.with_name(f"{path.stem}.corrupt-{timestamp}{path.suffix}")
            path.replace(backup)
            return ExternalProcessingAuditLog()

    @staticmethod
    def user_key_digest(user_key: str) -> str:
        return hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]

    def _path(self, user_key: str) -> Path:
        return self.root_dir / f"{self.user_key_digest(user_key)}.json"
