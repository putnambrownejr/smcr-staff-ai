from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.schemas.family_readiness import (
    FamilyReadinessChecklistItem,
    FamilyReadinessContact,
    FamilyReadinessContactUpsertRequest,
    FamilyReadinessEvent,
    FamilyReadinessEventCreateRequest,
    FamilyReadinessEventUpdateRequest,
    FamilyReadinessGlossaryEntry,
    FamilyReadinessGlossaryUpsertRequest,
    FamilyReadinessItemCreateRequest,
    FamilyReadinessItemOrderRequest,
    FamilyReadinessItemUpdateRequest,
    FamilyReadinessMilestoneUpdateRequest,
)
from app.services.family_readiness.builder import build_event
from app.services.session.handoff_store import is_valid_user_key


class FamilyReadinessStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list(self, user_key: str) -> list[FamilyReadinessEvent]:
        if not is_valid_user_key(user_key):
            return []
        prefix = f"{_user_digest(user_key)}-"
        records = [
            FamilyReadinessEvent.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.root_dir.glob(f"{prefix}*.json")
        ]
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    def create(self, request: FamilyReadinessEventCreateRequest) -> FamilyReadinessEvent:
        if not is_valid_user_key(request.user_key):
            raise ValueError("Invalid user_key.")
        event = build_event(request)
        self._write(event)
        return event

    def get(self, user_key: str, event_id: str) -> FamilyReadinessEvent | None:
        if not is_valid_user_key(user_key) or not _safe_id(event_id):
            return None
        path = self._path(user_key, event_id)
        if not path.exists():
            return None
        return FamilyReadinessEvent.model_validate_json(path.read_text(encoding="utf-8"))

    def update_event(
        self,
        user_key: str,
        event_id: str,
        request: FamilyReadinessEventUpdateRequest | dict[str, Any],
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        parsed = FamilyReadinessEventUpdateRequest.model_validate(request)
        values = parsed.model_dump(exclude_none=True)
        updated = event.model_copy(update={**values, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def add_item(
        self,
        user_key: str,
        event_id: str,
        request: FamilyReadinessItemCreateRequest,
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        item = FamilyReadinessChecklistItem(
            item_id=secrets.token_hex(8),
            origin="user",
            **request.model_dump(),
        )
        return self._replace(event, items=[*event.items, item])

    def update_item(
        self,
        user_key: str,
        event_id: str,
        item_id: str,
        request: FamilyReadinessItemUpdateRequest | dict[str, Any],
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        parsed = FamilyReadinessItemUpdateRequest.model_validate(request)
        found = False
        items: list[FamilyReadinessChecklistItem] = []
        for item in event.items:
            if item.item_id == item_id:
                found = True
                item = item.model_copy(update=parsed.model_dump(exclude_none=True))
            items.append(item)
        if not found:
            raise ValueError(f"Unknown readiness item: {item_id}")
        return self._replace(event, items=items)

    def reorder_items(
        self,
        user_key: str,
        event_id: str,
        request: FamilyReadinessItemOrderRequest,
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        if len(request.item_ids) != len(set(request.item_ids)) or set(request.item_ids) != {
            item.item_id for item in event.items
        }:
            raise ValueError("Item order must contain every checklist item exactly once.")
        by_id = {item.item_id: item for item in event.items}
        return self._replace(event, items=[by_id[item_id] for item_id in request.item_ids])

    def upsert_contact(
        self,
        user_key: str,
        event_id: str,
        request: FamilyReadinessContactUpsertRequest,
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        contact_id = request.contact_id or secrets.token_hex(8)
        contact = FamilyReadinessContact(
            contact_id=contact_id,
            **request.model_dump(exclude={"contact_id"}),
        )
        contacts = [contact if item.contact_id == contact_id else item for item in event.contacts]
        if not any(item.contact_id == contact_id for item in event.contacts):
            contacts.append(contact)
        return self._replace(event, contacts=contacts)

    def delete_contact(self, user_key: str, event_id: str, contact_id: str) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        contacts = [item for item in event.contacts if item.contact_id != contact_id]
        if len(contacts) == len(event.contacts):
            raise ValueError(f"Unknown readiness contact: {contact_id}")
        return self._replace(event, contacts=contacts)

    def upsert_glossary(
        self,
        user_key: str,
        event_id: str,
        request: FamilyReadinessGlossaryUpsertRequest,
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        entry = FamilyReadinessGlossaryEntry(**request.model_dump())
        entries = [entry if item.term.casefold() == entry.term.casefold() else item for item in event.glossary]
        if not any(item.term.casefold() == entry.term.casefold() for item in event.glossary):
            entries.append(entry)
        return self._replace(event, glossary=entries)

    def delete_glossary(self, user_key: str, event_id: str, term: str) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        entries = [item for item in event.glossary if item.term.casefold() != term.casefold()]
        if len(entries) == len(event.glossary):
            raise ValueError(f"Unknown readiness glossary term: {term}")
        return self._replace(event, glossary=entries)

    def update_milestone(
        self,
        user_key: str,
        event_id: str,
        milestone_id: str,
        request: FamilyReadinessMilestoneUpdateRequest,
    ) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        if not any(item.milestone_id == milestone_id for item in event.milestones):
            raise ValueError(f"Unknown readiness milestone: {milestone_id}")
        values = request.model_dump(exclude_none=True)
        milestones = [
            item.model_copy(update=values) if item.milestone_id == milestone_id else item for item in event.milestones
        ]
        return self._replace(event, milestones=milestones)

    def delete(self, user_key: str, event_id: str) -> bool:
        if not is_valid_user_key(user_key) or not _safe_id(event_id):
            return False
        path = self._path(user_key, event_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _replace(self, event: FamilyReadinessEvent, **updates: Any) -> FamilyReadinessEvent:
        updated = event.model_copy(update={**updates, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def _require(self, user_key: str, event_id: str) -> FamilyReadinessEvent:
        event = self.get(user_key, event_id)
        if event is None:
            raise ValueError(f"Unknown family readiness event: {event_id}")
        return event

    def _write(self, event: FamilyReadinessEvent) -> None:
        self._path(event.user_key, event.event_id).write_text(
            event.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _path(self, user_key: str, event_id: str) -> Path:
        return self.root_dir / f"{_user_digest(user_key)}-{event_id}.json"


def _user_digest(user_key: str) -> str:
    return hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]


def _safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"-", "_"} for character in value)
