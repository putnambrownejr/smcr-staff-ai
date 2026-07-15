from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CapabilityAuditRecord(BaseModel):
    undo_token: str
    user_key: str
    operation: str
    undo_kind: str
    target_id: str
    parent_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    used_at: datetime | None = None


class CapabilityAuditStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        *,
        user_key: str,
        operation: str,
        undo_kind: str,
        target_id: str,
        parent_id: str | None = None,
    ) -> CapabilityAuditRecord:
        record = CapabilityAuditRecord(
            undo_token=secrets.token_urlsafe(24),
            user_key=user_key,
            operation=operation,
            undo_kind=undo_kind,
            target_id=target_id,
            parent_id=parent_id,
        )
        records = self._read(user_key)
        records.append(record)
        self._write(user_key, records[-250:])
        return record

    def get_active(self, user_key: str, undo_token: str) -> CapabilityAuditRecord | None:
        return next(
            (record for record in self._read(user_key) if record.undo_token == undo_token and record.used_at is None),
            None,
        )

    def mark_used(self, user_key: str, undo_token: str) -> None:
        records = self._read(user_key)
        now = datetime.now(UTC)
        updated = [
            record.model_copy(update={"used_at": now}) if record.undo_token == undo_token else record
            for record in records
        ]
        self._write(user_key, updated)

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root / f"{digest}.json"

    def _read(self, user_key: str) -> list[CapabilityAuditRecord]:
        path = self._path(user_key)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [CapabilityAuditRecord.model_validate(item) for item in payload.get("records", [])]

    def _write(self, user_key: str, records: list[CapabilityAuditRecord]) -> None:
        payload = {"records": [record.model_dump(mode="json") for record in records]}
        self._path(user_key).write_text(json.dumps(payload, indent=2), encoding="utf-8")
