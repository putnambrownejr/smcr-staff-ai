"""Persist dashboard-only editor state separately from profile and journal data."""

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.services.session.handoff_store import is_valid_user_key

router = APIRouter(prefix="/dashboard/editors", dependencies=[LocalApiKeyDependency])


class EditorState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    staffLaneNotes: dict[str, str] = Field(default_factory=dict)
    staffLaneContacts: dict[str, list[dict[str, JsonValue]]] = Field(default_factory=dict)
    staffLaneDoctrineByKey: dict[str, list[dict[str, JsonValue]]] = Field(default_factory=dict)
    staffLaneResourcesByKey: dict[str, list[dict[str, JsonValue]]] = Field(default_factory=dict)
    staffLanePromptsByKey: dict[str, list[dict[str, JsonValue]]] = Field(default_factory=dict)
    gearItems: list[dict[str, JsonValue]] = Field(default_factory=list)
    promptPacks: list[dict[str, JsonValue]] = Field(default_factory=list)
    tzSelected: list[str] = Field(default_factory=list, max_length=10)
    customTz: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def limit_size(self) -> "EditorState":
        if len(self.model_dump_json().encode()) > 1_000_000:
            raise ValueError("Dashboard editor data exceeds the 1 MB limit.")
        return self


def _path(user_key: str) -> Path:
    if not is_valid_user_key(user_key):
        raise HTTPException(422, "Invalid user key.")
    digest = hashlib.sha256(user_key.encode()).hexdigest()[:24]
    return Path(get_settings().user_docs_dir) / "Workspace" / f"{digest}.json"


@router.get("/{user_key}", response_model=EditorState)
def get_editors(user_key: str) -> EditorState:
    path = _path(user_key)
    if not path.exists():
        raise HTTPException(404, "No saved editor data yet.")
    return EditorState.model_validate_json(path.read_text(encoding="utf-8"))


@router.put("/{user_key}", response_model=EditorState)
def save_editors(user_key: str, state: EditorState) -> EditorState:
    path = _path(user_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(state.model_dump_json())
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return state
