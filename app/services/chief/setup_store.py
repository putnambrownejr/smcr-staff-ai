from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.chief_setup import ChiefSetup, ChiefSetupUpsertRequest
from app.services.session.handoff_store import is_valid_user_key


class ChiefSetupStore:
    """File-per-user JSON store for each user's Chief of Staff standing context."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> ChiefSetup | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return ChiefSetup.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(self, user_key: str, request: ChiefSetupUpsertRequest) -> ChiefSetup:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        setup = ChiefSetup(
            user_key=user_key,
            unit=request.unit.strip(),
            billet=request.billet.strip(),
            echelon=request.echelon.strip(),
            drill_schedule=request.drill_schedule.strip(),
            commander_intent=request.commander_intent.strip(),
            priorities=_clean_list(request.priorities),
            battle_rhythm=_clean_list(request.battle_rhythm),
            watch_items=_clean_list(request.watch_items),
            output_format=request.output_format.strip() or "Naval letter",
            tone=request.tone.strip() or "Direct and professional",
            standing_notes=request.standing_notes.strip(),
            updated_at=datetime.now(UTC),
        )
        self._path(user_key).write_text(setup.model_dump_json(indent=2), encoding="utf-8")
        return setup

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


def _clean_list(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in items:
        value = raw.strip()
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        result.append(value)
    return result


def is_configured(setup: ChiefSetup | None) -> bool:
    if setup is None:
        return False
    return any(
        [
            setup.unit,
            setup.billet,
            setup.commander_intent,
            setup.priorities,
            setup.battle_rhythm,
            setup.watch_items,
            setup.standing_notes,
        ]
    )


def build_chief_briefing_block(setup: ChiefSetup) -> str:
    """Render the setup into a copy-paste Chief of Staff prompt for any chatbot.

    The block is self-contained: paste it as the first message in ChatGPT,
    Claude, Gemini, etc. to get a Chief of Staff that already knows the user's
    unit, priorities, battle rhythm, and preferences.
    """
    lines: list[str] = []
    lines.append("You are my Chief of Staff for reserve Marine Corps staff work.")
    lines.append(
        "Act as a senior staff coordinator: track my priorities, battle rhythm, "
        "due-outs, and readiness, and keep me ahead of suspenses. Give specific, "
        "actionable guidance grounded in public Marine Corps references. When you "
        "cite a regulation, name it by publication number; if you are unsure it is "
        "current, say so."
    )
    lines.append("")
    lines.append("## My context")
    context_rows = [
        ("Unit", setup.unit),
        ("Billet", setup.billet),
        ("Echelon", setup.echelon),
        ("Drill schedule", setup.drill_schedule),
    ]
    for label, value in context_rows:
        if value:
            lines.append(f"- {label}: {value}")
    if setup.commander_intent:
        lines.append(f"- Commander's intent / focus: {setup.commander_intent}")

    if setup.priorities:
        lines.append("")
        lines.append("## My current priorities")
        for item in setup.priorities:
            lines.append(f"- {item}")

    if setup.battle_rhythm:
        lines.append("")
        lines.append("## Recurring battle rhythm")
        for item in setup.battle_rhythm:
            lines.append(f"- {item}")

    if setup.watch_items:
        lines.append("")
        lines.append("## Watch items (keep me ahead of these)")
        for item in setup.watch_items:
            lines.append(f"- {item}")

    lines.append("")
    lines.append("## How I want you to work")
    lines.append(f"- Default output format for drafts: {setup.output_format}")
    lines.append(f"- Tone: {setup.tone}")
    if setup.standing_notes:
        lines.append(f"- Standing notes: {setup.standing_notes}")

    lines.append("")
    lines.append(
        "UNCLASSIFIED only. Do not ask for or use classified information, CUI, "
        "COMSEC, real frequencies, call signs, or PII. Everything you produce is "
        "an advisory draft I will verify against current official sources before acting."
    )
    lines.append("")
    lines.append("Start by asking me what I need help with this drill period.")
    return "\n".join(lines)
