import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from app.core.security import DEFAULT_WARNINGS
from app.schemas.product_templates import (
    CreateManualProductTemplateRequest,
    CreateProductTemplateFromContextRequest,
    ProductTemplateRecord,
)
from app.services.storage.local_context_store import LocalContextStore

TEMPLATE_ID_PATTERN = re.compile(r"^[a-f0-9]{16}$")
MAX_EXCERPT_CHARS = 1500


class ProductTemplateRepository:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ProductTemplateRecord]:
        items = [
            ProductTemplateRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def get(self, template_id: str) -> ProductTemplateRecord | None:
        if not is_valid_template_id(template_id):
            return None
        path = self._path(template_id)
        if not path.exists():
            return None
        return ProductTemplateRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def delete(self, template_id: str) -> bool:
        if not is_valid_template_id(template_id):
            return False
        path = self._path(template_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def create_from_context(
        self,
        request: CreateProductTemplateFromContextRequest,
        context_store: LocalContextStore,
    ) -> ProductTemplateRecord:
        source_item = context_store.get(request.context_id)
        if source_item is None:
            raise ValueError(f"Unknown local context item: {request.context_id}")
        preview = context_store.read_preview(request.context_id, max_chars=MAX_EXCERPT_CHARS) or ""
        reusable_headings = request.reusable_headings or derive_reusable_headings(preview)
        reusable_guidance = request.reusable_guidance or default_guidance(
            request.template_name,
            preview_available=bool(preview),
        )
        warnings = sorted(
            set(
                [
                    *DEFAULT_WARNINGS,
                    (
                        "Local example templates are advisory aids. Verify routing, "
                        "unit names, dates, and authorities before reuse."
                    ),
                    *source_item.warnings,
                ]
            )
        )
        now = datetime.now(UTC)
        record = ProductTemplateRecord(
            template_id=_template_id_from(request.template_name, request.context_id),
            template_name=request.template_name.strip(),
            template_type=request.template_type,
            created_at=now,
            updated_at=now,
            source_context_id=source_item.context_id,
            source_filename=source_item.filename,
            description=request.description,
            tags=request.tags,
            audience_hint=request.audience_hint,
            preferred_format=request.preferred_format,
            reusable_headings=reusable_headings,
            reusable_guidance=reusable_guidance,
            example_excerpt=preview or None,
            warnings=warnings,
        )
        self._write(record)
        return record

    def create_manual(self, request: CreateManualProductTemplateRequest) -> ProductTemplateRecord:
        reusable_guidance = request.reusable_guidance or default_guidance(
            request.template_name,
            preview_available=bool(request.example_excerpt),
        )
        now = datetime.now(UTC)
        record = ProductTemplateRecord(
            template_id=_template_id_from(request.template_name, request.description or request.template_type.value),
            template_name=request.template_name.strip(),
            template_type=request.template_type,
            created_at=now,
            updated_at=now,
            description=request.description,
            tags=request.tags,
            audience_hint=request.audience_hint,
            preferred_format=request.preferred_format,
            reusable_headings=request.reusable_headings,
            reusable_guidance=reusable_guidance,
            example_excerpt=(request.example_excerpt or "")[:MAX_EXCERPT_CHARS] or None,
            warnings=[
                *DEFAULT_WARNINGS,
                "Manual templates are local reusable scaffolds. Validate final routing and authority before release.",
            ],
        )
        self._write(record)
        return record

    def _path(self, template_id: str) -> Path:
        return self.root_dir / f"{template_id}.json"

    def _write(self, record: ProductTemplateRecord) -> None:
        self._path(record.template_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")


def is_valid_template_id(template_id: str) -> bool:
    return bool(TEMPLATE_ID_PATTERN.fullmatch(template_id))


def derive_reusable_headings(preview: str) -> list[str]:
    headings: list[str] = []
    for raw_line in preview.splitlines():
        line = raw_line.strip()
        if len(line) < 3 or len(line) > 90:
            continue
        if line.startswith("#"):
            headings.append(line.lstrip("# ").strip())
        elif line.endswith(":") and len(line.split()) <= 8:
            headings.append(line[:-1].strip())
        elif re.match(r"^\d+[\.\)]\s+\S", line):
            headings.append(line)
        elif line.upper() == line and len(line.split()) <= 8 and any(char.isalpha() for char in line):
            headings.append(line.title())
    unique: list[str] = []
    for heading in headings:
        if heading not in unique:
            unique.append(heading)
    return unique[:12]


def default_guidance(template_name: str, preview_available: bool) -> list[str]:
    guidance = [
        f"Use {template_name} as a structure and tone reference, not as a source of authority.",
        "Strip or replace unit-specific names, dates, routing, phone numbers, and stale references before reuse.",
    ]
    if preview_available:
        guidance.append("Preserve useful section ordering and briefing rhythm where it still fits the new task.")
    else:
        guidance.append("Use the stored metadata and user notes to rebuild the reusable structure manually.")
    return guidance


def _template_id_from(*parts: str) -> str:
    raw = "::".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:16]
