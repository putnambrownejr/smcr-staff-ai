from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.custom_mos_recipe import CustomMosRecipe, CustomMosRecipeStore
from app.services.session.handoff_store import is_valid_user_key


class CustomMosRecipeStoreService:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get(self, user_key: str) -> list[CustomMosRecipe]:
        if not is_valid_user_key(user_key):
            return []
        path = self._path(user_key)
        if not path.exists():
            return []
        store = CustomMosRecipeStore.model_validate_json(path.read_text(encoding="utf-8"))
        return store.recipes

    def add(self, user_key: str, recipe: CustomMosRecipe) -> list[CustomMosRecipe]:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        existing = self.get(user_key)
        existing = [r for r in existing if r.mos_code.lower() != recipe.mos_code.lower()]
        existing.append(recipe)
        store = CustomMosRecipeStore(
            user_key=user_key,
            recipes=existing,
            updated_at=datetime.now(UTC),
        )
        self._path(user_key).write_text(store.model_dump_json(indent=2), encoding="utf-8")
        return existing

    def delete(self, user_key: str, mos_code: str) -> list[CustomMosRecipe]:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        existing = self.get(user_key)
        filtered = [r for r in existing if r.mos_code.lower() != mos_code.lower()]
        store = CustomMosRecipeStore(
            user_key=user_key,
            recipes=filtered,
            updated_at=datetime.now(UTC),
        )
        self._path(user_key).write_text(store.model_dump_json(indent=2), encoding="utf-8")
        return filtered

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"
