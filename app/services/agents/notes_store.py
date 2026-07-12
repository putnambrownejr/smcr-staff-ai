from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Literal

from app.schemas.agent_notes import AgentNotesResponse
from app.services.session.handoff_store import is_valid_user_key

logger = logging.getLogger(__name__)

NoteKind = Literal["agent", "skill"]


class AgentNotesStore:
    """User-editable notes on catalog agents/skills, meant to be copied back
    into the agent's or skill's own file -- not a runtime behavior change,
    just a place to jot feedback while using the AI catalog page."""

    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> AgentNotesResponse:
        if not is_valid_user_key(user_key):
            return AgentNotesResponse()
        path = self._path(user_key)
        if not path.exists():
            return AgentNotesResponse()
        try:
            return AgentNotesResponse.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            logger.warning("Could not load agent notes for %s", user_key)
            return AgentNotesResponse()

    def set_note(self, user_key: str, kind: NoteKind, item_id: str, note: str) -> AgentNotesResponse:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        data = self.get(user_key)
        target = data.agent_notes if kind == "agent" else data.skill_notes
        if note.strip():
            target[item_id] = note
        else:
            target.pop(item_id, None)
        self._save(user_key, data)
        return data

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.storage_dir / f"{digest}.json"

    def _save(self, user_key: str, data: AgentNotesResponse) -> None:
        self._path(user_key).write_text(data.model_dump_json(indent=2), encoding="utf-8")
