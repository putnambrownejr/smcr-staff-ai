from __future__ import annotations

import hashlib
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml

from app.schemas.user_docs import (
    ProjectDescriptor,
    UserDocCategory,
    UserDocCreateRequest,
    UserDocEntry,
    UserDocUpdateRequest,
)
from app.services.session.handoff_store import is_valid_user_key

logger = logging.getLogger(__name__)

_CATEGORY_FOLDER = {
    UserDocCategory.notebook: "Notebook",
    UserDocCategory.fitreps: "FitReps",
    UserDocCategory.generations: "Generations",
}

_FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "untitled"


class UserDocsStore:
    """A file-per-entry markdown store, gitignored, under `settings.user_docs_dir`.

    Distinct from the JSON-blob-per-domain stores used elsewhere in this app:
    entries here are real, readable `.md` files with a YAML front-matter header,
    organized as `{root}/{Category}/{user_digest}/{id}.md`, so the personal
    notebook, FitRep drafts, and staff-product generations created from the
    Bench/Files page are actual files a user can also browse/edit outside the
    app -- and can be moved into `projects/{name}/products/` on request.
    """

    def __init__(self, root_dir: str | Path, projects_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.projects_dir = Path(projects_dir)
        for folder in _CATEGORY_FOLDER.values():
            (self.root_dir / folder).mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def list_category(self, category: UserDocCategory, user_key: str) -> list[UserDocEntry]:
        if not is_valid_user_key(user_key):
            return []
        user_dir = self._user_dir(category, user_key)
        if not user_dir.exists():
            return []
        entries = []
        for path in sorted(user_dir.glob("*.md")):
            entry = self._read(path)
            if entry is not None:
                entries.append(entry)
        return sorted(entries, key=lambda e: e.updated_at, reverse=True)

    def get(self, category: UserDocCategory, user_key: str, doc_id: str) -> UserDocEntry | None:
        if not is_valid_user_key(user_key) or not _is_safe_id(doc_id):
            return None
        return self._read(self._doc_path(category, user_key, doc_id))

    def create(self, category: UserDocCategory, user_key: str, request: UserDocCreateRequest) -> UserDocEntry:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        now = datetime.now(UTC)
        entry = UserDocEntry(
            id=uuid.uuid4().hex[:12],
            category=category,
            title=request.title,
            body=request.body,
            fields=request.fields,
            created_at=now,
            updated_at=now,
        )
        self._write(self._doc_path(category, user_key, entry.id), entry)
        return entry

    def update(
        self,
        category: UserDocCategory,
        user_key: str,
        doc_id: str,
        request: UserDocUpdateRequest,
    ) -> UserDocEntry | None:
        existing = self.get(category, user_key, doc_id)
        if existing is None:
            return None
        updated = existing.model_copy(
            update={
                "title": request.title if request.title is not None else existing.title,
                "body": request.body if request.body is not None else existing.body,
                "fields": request.fields if request.fields is not None else existing.fields,
                "updated_at": datetime.now(UTC),
            }
        )
        self._write(self._doc_path(category, user_key, doc_id), updated)
        return updated

    def delete(self, category: UserDocCategory, user_key: str, doc_id: str) -> bool:
        if not is_valid_user_key(user_key) or not _is_safe_id(doc_id):
            return False
        path = self._doc_path(category, user_key, doc_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_projects(self) -> list[ProjectDescriptor]:
        if not self.projects_dir.exists():
            return []
        projects: list[ProjectDescriptor] = []
        for path in sorted((p for p in self.projects_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
            descriptor = ProjectDescriptor(name=path.name)
            metadata_path = path / ".smcr-project.json"
            if metadata_path.exists():
                try:
                    candidate = ProjectDescriptor.model_validate_json(metadata_path.read_text(encoding="utf-8"))
                    if candidate.name == path.name:
                        descriptor = candidate
                    else:
                        logger.warning("Ignoring mismatched project metadata: %s", metadata_path)
                except (OSError, ValueError):
                    logger.warning("Ignoring invalid project metadata: %s", metadata_path)
            projects.append(descriptor)
        return projects

    def save_to_project(
        self,
        category: UserDocCategory,
        user_key: str,
        doc_id: str,
        project: str,
    ) -> Path:
        entry = self.get(category, user_key, doc_id)
        if entry is None:
            raise ValueError(f"Unknown user doc: {doc_id}")
        project_slug = _slugify(project)
        if not project_slug:
            raise ValueError("Invalid project name.")
        project_dir = (self.projects_dir / project_slug).resolve()
        if not project_dir.is_relative_to(self.projects_dir.resolve()):
            raise ValueError("Invalid project name.")
        products_dir = project_dir / "products"
        is_new_project = not project_dir.exists()
        products_dir.mkdir(parents=True, exist_ok=True)
        if is_new_project:
            readme = project_dir / "README.md"
            readme.write_text(
                f"# {project}\n\nCreated {datetime.now(UTC):%Y-%m-%d} via Save to project.\n",
                encoding="utf-8",
            )
        target = products_dir / f"{_slugify(entry.title)}.md"
        target.write_text(_render_markdown(entry), encoding="utf-8")
        self.delete(category, user_key, doc_id)
        return Path(project_slug) / "products" / target.name

    def _doc_path(self, category: UserDocCategory, user_key: str, doc_id: str) -> Path:
        return self._user_dir(category, user_key) / f"{doc_id}.md"

    def _user_dir(self, category: UserDocCategory, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / _CATEGORY_FOLDER[category] / digest

    def _write(self, path: Path, entry: UserDocEntry) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_markdown(entry), encoding="utf-8")

    def _read(self, path: Path) -> UserDocEntry | None:
        if not path.exists():
            return None
        try:
            raw = path.read_text(encoding="utf-8")
            match = _FRONT_MATTER_RE.match(raw)
            if not match:
                return None
            meta = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return UserDocEntry(
                id=meta["id"],
                category=meta["category"],
                title=meta.get("title", "Untitled"),
                body=body.strip("\n"),
                fields=meta.get("fields") or {},
                created_at=meta["created_at"],
                updated_at=meta["updated_at"],
            )
        except Exception:
            logger.warning("Could not parse user doc file: %s", path)
            return None


def _is_safe_id(doc_id: str) -> bool:
    return bool(re.fullmatch(r"[a-f0-9]{6,40}", doc_id))


def _render_markdown(entry: UserDocEntry) -> str:
    meta = {
        "id": entry.id,
        "category": entry.category.value,
        "title": entry.title,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
        "fields": entry.fields,
    }
    front_matter = yaml.safe_dump(meta, sort_keys=False, default_flow_style=False, allow_unicode=True)
    return f"---\n{front_matter}---\n\n{entry.body}\n"
