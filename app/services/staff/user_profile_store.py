from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.user_profile import FormatPreference, UserProfile
from app.services.session.handoff_store import is_valid_user_key


class UserProfileStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> UserProfile | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return UserProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def upsert(
        self,
        user_key: str,
        *,
        billet: str = "",
        unit: str = "",
        mos: str = "",
        format_preference: FormatPreference = FormatPreference.naval_letter,
        one_number_one_rule: bool = True,
        style_notes: str = "",
    ) -> UserProfile:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        profile = UserProfile(
            user_key=user_key,
            billet=billet.strip(),
            unit=unit.strip(),
            mos=mos.strip(),
            format_preference=format_preference,
            one_number_one_rule=one_number_one_rule,
            style_notes=style_notes.strip(),
            updated_at=datetime.now(UTC),
        )
        self._path(user_key).write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        return profile

    def delete(self, user_key: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        path = self._path(user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_keys(self) -> list[str]:
        """Return all stored user_key values, sorted alphabetically."""
        keys: list[str] = []
        for path in self.root_dir.glob("*.json"):
            try:
                profile = UserProfile.model_validate_json(path.read_text(encoding="utf-8"))
                keys.append(profile.user_key)
            except Exception:  # noqa: BLE001
                continue
        return sorted(keys)

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"
