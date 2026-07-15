"""Generate one editable Markdown scaffold per system-template catalog record."""

from __future__ import annotations

from pathlib import Path

from app.schemas.product_templates import ProductTemplateRecord
from app.services.templates.system_template_catalog import SystemTemplateCatalog

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "data" / "seed" / "system_templates.example.yaml"
OUTPUT_DIR = REPO_ROOT / "data" / "templates" / "system"
FOOTER = "DRAFT — Verify all references against current official sources before acting."


def render_template(record: ProductTemplateRecord) -> str:
    title = str(record.template_name)
    lines = [
        f"# {title}",
        "",
        f"**Template ID:** `{record.template_id}`  ",
        f"**Type:** `{record.template_type.value}`",
        "",
    ]
    if record.description:
        lines.extend([str(record.description), ""])
    if record.audience_hint:
        lines.extend([f"**Intended audience:** {record.audience_hint}", ""])
    lines.extend(["## Working scaffold", ""])
    for heading in record.reusable_headings:
        lines.extend([f"### {heading}", "", "- [Add reviewed content.]", ""])
    if record.reusable_guidance:
        lines.extend(["## Guidance", ""])
        lines.extend(f"- {item}" for item in record.reusable_guidance)
        lines.append("")
    if record.warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {item}" for item in record.warnings)
        lines.append("")
    lines.extend(["---", "", FOOTER, ""])
    return "\n".join(lines)


def main() -> None:
    catalog = SystemTemplateCatalog.from_yaml(CATALOG_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    expected = {f"{record.template_id}.md" for record in catalog.list()}
    for stale in OUTPUT_DIR.glob("*.md"):
        if stale.name not in expected:
            stale.unlink()
    for record in catalog.list():
        path = OUTPUT_DIR / f"{record.template_id}.md"
        path.write_text(render_template(record), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
