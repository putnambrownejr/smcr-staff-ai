import hashlib
import re
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.security import DEFAULT_WARNINGS, detect_pii_input, detect_sensitive_input, redact_pii
from app.schemas.context import LocalContextMetadata

MAX_PREVIEW_CHARS = 4000
CONTEXT_ID_PATTERN = re.compile(r"^[a-f0-9]{16}$")
DEFAULT_MAX_UPLOAD_BYTES = 10_000_000


class LocalContextStore:
    """Filesystem-backed store for user working context.

    Uploaded context is intentionally separate from canonical doctrine/document ingestion.
    It can be referenced by future agent requests, but it does not alter org, doctrine,
    document, exercise, or agent registry structure.
    """

    def __init__(self, root_dir: str | Path, max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES) -> None:
        self.root_dir = Path(root_dir)
        self.max_upload_bytes = max_upload_bytes
        self.files_dir = self.root_dir / "files"
        self.metadata_dir = self.root_dir / "metadata"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        tags: list[str] | None = None,
        document_type: str = "other",
        consent_ack: bool = False,
        review_date: date | None = None,
        expiration_date: date | None = None,
    ) -> LocalContextMetadata:
        if len(content) > self.max_upload_bytes:
            raise ValueError(f"Upload exceeds max_upload_bytes={self.max_upload_bytes}.")
        digest = hashlib.sha256(content).hexdigest()
        context_id = digest[:16]
        safe_name = _safe_filename(filename)
        file_path = self.files_dir / f"{context_id}-{safe_name}"
        file_path.write_bytes(content)

        warnings = [*DEFAULT_WARNINGS]
        text = _decode_preview(content) if _is_text_like(content_type, safe_name) else ""
        warnings.extend(detect_sensitive_input(text))
        contains_pii = bool(detect_pii_input(text))

        metadata = LocalContextMetadata(
            context_id=context_id,
            filename=safe_name,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(content),
            sha256=digest,
            uploaded_at=datetime.now(UTC),
            tags=tags or [],
            document_type=document_type,
            contains_pii=contains_pii,
            consent_ack=consent_ack,
            review_date=review_date,
            expiration_date=expiration_date,
            warnings=warnings,
        )
        self._metadata_path(context_id).write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return metadata

    def list(self) -> list[LocalContextMetadata]:
        items = [
            LocalContextMetadata.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.metadata_dir.glob("*.json"))
        ]
        return sorted(items, key=lambda item: item.uploaded_at, reverse=True)

    def get(self, context_id: str) -> LocalContextMetadata | None:
        if not is_valid_context_id(context_id):
            return None
        path = self._metadata_path(context_id)
        if not path.exists():
            return None
        return LocalContextMetadata.model_validate_json(path.read_text(encoding="utf-8"))

    def read_preview(self, context_id: str, max_chars: int = MAX_PREVIEW_CHARS) -> str | None:
        if not is_valid_context_id(context_id):
            return None
        metadata = self.get(context_id)
        if metadata is None:
            return None
        file_path = self._file_path_for(metadata)
        if file_path is None:
            return None
        if _is_text_like(metadata.content_type, metadata.filename):
            return redact_pii(_decode_preview(file_path.read_bytes()))[:max_chars]
        return _binary_preview(metadata)

    def delete(self, context_id: str) -> bool:
        if not is_valid_context_id(context_id):
            return False
        found = False
        metadata_path = self._metadata_path(context_id)
        metadata = self.get(context_id)
        if metadata_path.exists():
            metadata_path.unlink()
            found = True
        file_path = self._file_path_for(metadata) if metadata is not None else None
        if file_path is not None and file_path.exists():
            file_path.unlink()
            found = True
        return found

    def _metadata_path(self, context_id: str) -> Path:
        return self.metadata_dir / f"{context_id}.json"

    def _file_path_for(self, metadata: LocalContextMetadata) -> Path | None:
        if not is_valid_context_id(metadata.context_id):
            return None
        candidate = self.files_dir / f"{metadata.context_id}-{metadata.filename}"
        try:
            candidate.resolve().relative_to(self.files_dir.resolve())
        except ValueError:
            return None
        return candidate


def parse_tags(raw_tags: str | None) -> list[str]:
    if raw_tags is None:
        return []
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def is_valid_context_id(context_id: str) -> bool:
    return bool(CONTEXT_ID_PATTERN.fullmatch(context_id))


def _decode_preview(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload.bin"
    return "".join(char if char.isalnum() or char in {".", "-", "_"} else "_" for char in name)


def _is_text_like(content_type: str, filename: str) -> bool:
    lowered = content_type.lower()
    suffix = Path(filename).suffix.lower()
    return lowered.startswith("text/") or suffix in {".txt", ".md", ".json", ".yaml", ".yml", ".csv"}


def _binary_preview(metadata: LocalContextMetadata) -> str:
    tags = ", ".join(metadata.tags) if metadata.tags else "none"
    return (
        f"Binary local context item: {metadata.filename}\n"
        f"Content type: {metadata.content_type}\n"
        f"Size bytes: {metadata.size_bytes}\n"
        f"Document type: {metadata.document_type}\n"
        f"Tags: {tags}\n"
        "No text preview is available for this media item."
    )
