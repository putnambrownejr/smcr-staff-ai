from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path

from app.schemas.resource_links import CATEGORY_LABELS, ResourceLink, ResourceLinkCategory, ResourceLinkCreate
from app.services.session.handoff_store import is_valid_user_key

logger = logging.getLogger(__name__)


class ResourceLinksStore:
    def __init__(self, storage_dir: str | Path, seed_path: str | Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._seed: list[ResourceLink] = _load_seed(Path(seed_path))

    def get_all(
        self,
        user_key: str,
        category: ResourceLinkCategory | None = None,
    ) -> list[ResourceLink]:
        user_links = self._load_user_links(user_key) if is_valid_user_key(user_key) else []
        all_links = [*self._seed, *user_links]
        if category is not None:
            all_links = [link for link in all_links if link.category == category]
        return sorted(all_links, key=lambda lnk: (CATEGORY_LABELS.get(lnk.category, ""), lnk.title.lower()))

    def add(self, user_key: str, create: ResourceLinkCreate) -> ResourceLink:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        link = ResourceLink(
            id=uuid.uuid4().hex[:8],
            title=create.title,
            url=create.url,
            category=create.category,
            description=create.description,
            is_seed=False,
            tags=create.tags,
        )
        user_links = self._load_user_links(user_key)
        user_links.append(link)
        self._save_user_links(user_key, user_links)
        return link

    def delete(self, user_key: str, link_id: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        user_links = self._load_user_links(user_key)
        filtered = [lnk for lnk in user_links if lnk.id != link_id]
        if len(filtered) == len(user_links):
            return False
        self._save_user_links(user_key, filtered)
        return True

    def _load_user_links(self, user_key: str) -> list[ResourceLink]:
        path = self._path(user_key)
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return [ResourceLink.model_validate(item) for item in raw]
        except Exception:
            logger.warning("Could not load user resource links for %s", user_key)
            return []

    def _save_user_links(self, user_key: str, links: list[ResourceLink]) -> None:
        path = self._path(user_key)
        path.write_text(
            json.dumps([link.model_dump() for link in links], indent=2),
            encoding="utf-8",
        )

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.storage_dir / f"{digest}.json"


def _load_seed(seed_path: Path) -> list[ResourceLink]:
    if not seed_path.exists():
        logger.warning("Resource links seed file not found: %s", seed_path)
        return []
    try:
        raw = json.loads(seed_path.read_text(encoding="utf-8"))
        return [ResourceLink.model_validate({**item, "is_seed": True}) for item in raw]
    except Exception:
        logger.warning("Could not parse resource links seed file: %s", seed_path)
        return []
