from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.product_templates import ProductTemplateRecord, SystemTemplateDetail, SystemTemplateSection

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATE_DIR = REPO_ROOT / "data" / "templates" / "system"


class SystemTemplateCatalog:
    def __init__(
        self,
        records: list[ProductTemplateRecord],
        details: dict[str, SystemTemplateDetail] | None = None,
        template_dir: str | Path = DEFAULT_TEMPLATE_DIR,
    ) -> None:
        self.records = records
        self.details = details or {}
        self.template_dir = Path(template_dir)

    @classmethod
    def from_dir(
        cls,
        detail_dir: str | Path,
        template_dir: str | Path = DEFAULT_TEMPLATE_DIR,
    ) -> SystemTemplateCatalog:
        """Build a curated catalog from the built-out detail YAMLs in ``detail_dir``.

        ``.list()``/``.get()`` return exactly the curated system templates.
        """
        details = _load_details(detail_dir, template_dir)
        records: list[ProductTemplateRecord] = sorted(
            details.values(), key=lambda detail: detail.template_name
        )
        return cls(records, details, template_dir)

    def list(self) -> list[ProductTemplateRecord]:
        return list(self.records)

    def get(self, template_id: str) -> ProductTemplateRecord | None:
        return next((record for record in self.records if record.template_id == template_id), None)

    def get_detail(self, template_id: str) -> SystemTemplateDetail | None:
        detail = self.details.get(template_id)
        if detail is not None:
            return detail
        record = self.get(template_id)
        if record is None:
            return None
        return SystemTemplateDetail(
            **record.model_dump(),
            source_path=_source_path(record.template_id, self.template_dir),
            guidance=record.reusable_guidance,
        )


def _load_details(detail_dir: str | Path | None, template_dir: str | Path) -> dict[str, SystemTemplateDetail]:
    if detail_dir is None:
        return {}
    path = Path(detail_dir)
    if not path.exists():
        return {}
    return {
        detail.template_id: detail
        for detail in (
            _detail_from_yaml(item, template_dir)
            for item in sorted(path.glob("*.yaml"))
        )
    }


def _detail_from_yaml(path: Path, template_dir: str | Path) -> SystemTemplateDetail:
    with open(path, encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    sections = [SystemTemplateSection.model_validate(item) for item in payload.get("sections", [])]
    guidance = list(payload.get("guidance") or [])
    template_id = str(payload["template_id"])
    source_path = _source_path(template_id, template_dir)
    return SystemTemplateDetail(
        template_id=template_id,
        template_name=payload["template_name"],
        template_type=payload["template_type"],
        description=payload.get("one_liner") or payload.get("when_to_use"),
        tags=["system", template_id.removeprefix("sys-"), str(payload["template_type"])],
        audience_hint=payload.get("audience_hint"),
        preferred_format=payload.get("preferred_format"),
        reusable_headings=[section.heading for section in sections],
        reusable_guidance=guidance,
        example_excerpt=_example_excerpt(sections),
        local_only=False,
        warnings=list(payload.get("warnings") or []),
        source_path=source_path,
        agent_handoff=payload.get("agent_handoff"),
        one_liner=payload.get("one_liner"),
        when_to_use=payload.get("when_to_use"),
        doctrine_refs=list(payload.get("doctrine_refs") or []),
        sections=sections,
        guidance=guidance,
    )


def _source_path(template_id: str, template_dir: str | Path) -> str:
    # The curated system templates are served by the content API, not a static .md file.
    # The dashboard viewer fetches the full detail (scaffold + example) from this path.
    return f"/product-templates/system/{template_id}"


def _example_excerpt(sections: list[SystemTemplateSection]) -> str | None:
    excerpt = "\n\n".join(
        f"{section.heading}\n{section.example.strip()}"
        for section in sections
        if section.example
    )
    return excerpt[:1500] or None
