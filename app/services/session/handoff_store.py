import hashlib
import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.core.security import DEFAULT_WARNINGS
from app.schemas.session import UserSessionHandoff

USER_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{1,80}$")


class SessionHandoffStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def upsert(self, handoff: UserSessionHandoff) -> UserSessionHandoff:
        if not is_valid_user_key(handoff.user_key):
            raise ValueError("Invalid user_key. Use 2-81 characters: letters, numbers, underscore, dash, dot, or @.")
        handoff.warnings = sorted(
            set([*handoff.warnings, *DEFAULT_WARNINGS, "Store minimum required user context only."])
        )
        # Publish only a completely written file. A failed save must leave the
        # previous handoff readable rather than truncating the user's continuity.
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.root_dir, suffix=".tmp", delete=False) as output:
                temporary = Path(output.name)
                output.write(handoff.model_dump_json(indent=2))
                output.flush()
                os.fsync(output.fileno())
            temporary.replace(self._path(handoff.user_key))
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return handoff

    def get(self, user_key: str) -> UserSessionHandoff | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key)
        if not path.exists():
            return None
        return UserSessionHandoff.model_validate_json(path.read_text(encoding="utf-8"))

    def delete(self, user_key: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        path = self._path(user_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode()).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"


def is_valid_user_key(user_key: str) -> bool:
    return bool(USER_KEY_PATTERN.fullmatch(user_key))
