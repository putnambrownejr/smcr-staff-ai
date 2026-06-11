from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.battle_rhythm import (
    BattleRhythmBoardResponse,
    BattleRhythmBoardUpsertRequest,
    BattleRhythmEntry,
    BattleRhythmEntryInput,
)
from app.services.session.handoff_store import is_valid_user_key


class BattleRhythmStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> BattleRhythmBoardResponse | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return BattleRhythmBoardResponse.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(self, user_key: str, request: BattleRhythmBoardUpsertRequest) -> BattleRhythmBoardResponse:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        existing = self.get(user_key)
        record = BattleRhythmBoardResponse(
            user_key=user_key,
            board_title=request.board_title.strip(),
            source_title=request.source_title,
            focus=_dedupe_strings(request.focus),
            assumption_log=_merge_entries(existing.assumption_log if existing else [], request.assumption_log),
            commander_decision_log=_merge_entries(
                existing.commander_decision_log if existing else [],
                request.commander_decision_log,
            ),
            question_log=_merge_entries(existing.question_log if existing else [], request.question_log),
            due_out_board=_merge_entries(existing.due_out_board if existing else [], request.due_out_board),
            next_touchpoint=request.next_touchpoint,
            context_note=request.context_note,
            updated_at=datetime.now(UTC),
            warnings=_dedupe_strings(request.warnings),
        )
        self._path(user_key).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"


def _merge_entries(
    existing: list[BattleRhythmEntry],
    incoming: list[BattleRhythmEntryInput],
) -> list[BattleRhythmEntry]:
    existing_by_text = {item.text.strip().lower(): item for item in existing}
    merged: list[BattleRhythmEntry] = []
    for item in incoming:
        key = item.text.strip().lower()
        prior = existing_by_text.get(key)
        merged.append(
            BattleRhythmEntry(
                entry_id=prior.entry_id if prior is not None else _entry_id(item),
                text=item.text.strip(),
                section=item.section,
                owner=item.owner,
                status=item.status,
                suspense_date=item.suspense_date,
                notes=_dedupe_strings(item.notes),
                source=item.source,
                updated_at=datetime.now(UTC),
            )
        )
    return merged


def _entry_id(item: BattleRhythmEntryInput) -> str:
    raw = "::".join(
        [
            item.text.strip().lower(),
            (item.section or "").strip().lower(),
            (item.owner or "").strip().lower(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
