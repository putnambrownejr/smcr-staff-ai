from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

from app.schemas.actions import (
    ActionItemRequest,
    ActionLinkRecord,
    ActionLinkRequest,
    ActionPriority,
    ActionRecord,
    ActionStatus,
    ActionUpdateRequest,
)


class ActionTracker:
    def __init__(self, root_dir: str | Path = "data/local_context/actions") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def track(self, actions: list[ActionItemRequest]) -> list[ActionRecord]:
        tracked = [self._record_from_request(action) for action in actions]
        for record in tracked:
            self._path(record.action_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return tracked

    def list(
        self,
        *,
        user_key: str | None = None,
        status: ActionStatus | None = None,
        include_closed: bool = False,
    ) -> list[ActionRecord]:
        records = [
            ActionRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        if user_key is not None:
            records = [record for record in records if record.user_key in {None, user_key}]
        if status is not None:
            records = [record for record in records if record.status == status]
        if not include_closed:
            records = [
                record
                for record in records
                if record.status not in {ActionStatus.complete, ActionStatus.archived}
            ]
        return sorted(records, key=_sort_key)

    def get(self, action_id: str) -> ActionRecord | None:
        path = self._path(action_id)
        if not path.exists():
            return None
        return ActionRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def update(self, action_id: str, update: ActionUpdateRequest) -> ActionRecord | None:
        record = self.get(action_id)
        if record is None:
            return None
        payload = update.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(record, key, value)
        record.updated_at = datetime.now(UTC)
        self._path(action_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def add_link(self, action_id: str, link: ActionLinkRequest) -> ActionRecord | None:
        record = self.get(action_id)
        if record is None:
            return None
        link_record = _link_record(link)
        record.links = [item for item in record.links if item.link_id != link_record.link_id]
        record.links.append(link_record)
        record.updated_at = datetime.now(UTC)
        self._path(action_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def remove_link(self, action_id: str, link_id: str) -> ActionRecord | None:
        record = self.get(action_id)
        if record is None:
            return None
        original_count = len(record.links)
        record.links = [item for item in record.links if item.link_id != link_id]
        if len(record.links) == original_count:
            return None
        record.updated_at = datetime.now(UTC)
        self._path(action_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def delete(self, action_id: str) -> bool:
        path = self._path(action_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _record_from_request(self, action: ActionItemRequest) -> ActionRecord:
        action_id = _action_id(action)
        existing = self.get(action_id)
        if existing is not None:
            payload = existing.model_dump()
            payload.update(action.model_dump())
            payload["action_id"] = action_id
            payload["updated_at"] = datetime.now(UTC)
            return ActionRecord(**payload)
        return ActionRecord(action_id=action_id, **action.model_dump())

    def _path(self, action_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in action_id)
        return self.root_dir / f"{safe_id}.json"


def _action_id(action: ActionItemRequest) -> str:
    seed = "|".join(
        [
            action.user_key or "",
            action.title,
            action.owner or "",
            action.category.value,
            action.suspense_date.isoformat() if action.suspense_date else "",
        ]
    )
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _sort_key(record: ActionRecord) -> tuple[int, date | datetime, str]:
    priority_rank = {
        ActionPriority.high: 0,
        ActionPriority.medium: 1,
        ActionPriority.low: 2,
    }
    when = record.suspense_date if record.suspense_date is not None else record.updated_at
    return (priority_rank[record.priority], when, record.title.lower())


def _link_record(link: ActionLinkRequest) -> ActionLinkRecord:
    seed = "|".join([link.link_type.value, link.label, link.target_id or "", link.url or ""])
    return ActionLinkRecord(
        link_id=hashlib.sha256(seed.encode()).hexdigest()[:20],
        link_type=link.link_type,
        label=link.label,
        target_id=link.target_id,
        url=link.url,
        notes=link.notes,
    )
