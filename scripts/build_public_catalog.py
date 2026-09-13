"""Build/check the explicit publication snapshot; never crawl user directories.

Run from the repository: uv run python scripts/build_public_catalog.py [--check]
The result is a shipped application asset, not a user work product.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.public_library.models import DRAFT_NOTICE, CatalogSnapshot, LibraryItem, SourceLink  # noqa: E402
from app.services.templates.system_template_catalog import SystemTemplateCatalog  # noqa: E402

REFERENCE_CATEGORIES = ("core_marine_doctrine", "correspondence_formatting", "operations_planning", "training_readiness")
TEMPLATE_IDS = (
    "sys-aar", "sys-command-update", "sys-conop", "sys-decision-brief",
    "sys-frago", "sys-naval-letter", "sys-opord", "sys-warno",
)
PROMPT_IDS = ("staff-writing", "source-checking")
REPO_URL = "https://github.com/putnambrownejr/smcr-staff-ai/blob/main/"
OUTPUT = REPO_ROOT / "app/public_library/catalog.json"


def source_digest(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    if path.is_symlink() or not path.resolve().is_relative_to(REPO_ROOT):
        raise ValueError("Publication sources must stay inside the repository.")
    # Normalize checkout line endings so Windows and Linux publish identical data.
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def build_snapshot() -> CatalogSnapshot:
    items: list[LibraryItem] = []
    manifest_path = "data/seed/doctrine_manifest.example.yaml"
    digest = source_digest(manifest_path)
    manifest = yaml.safe_load((REPO_ROOT / manifest_path).read_text(encoding="utf-8"))
    categories = {entry["id"]: entry for entry in manifest["categories"]}
    for category_id in REFERENCE_CATEGORIES:
        category = categories[category_id]
        if category.get("cui_flag") is not False or category.get("classification_label") != "UNCLASSIFIED":
            raise ValueError(f"Reference category {category_id} is not explicitly public UNCLASSIFIED.")
        for reference in category["source_refs"]:
            url = reference["url"]
            host = urlsplit(url).hostname or ""
            if reference.get("cac_required") is not False or not host.endswith((".mil", ".gov")):
                raise ValueError("Only explicitly CAC-free official public reference links can be published.")
            identity = hashlib.sha256(url.encode()).hexdigest()[:12]
            content = (
                f"# {reference['title']}\n\n{reference.get('scope_note', '')}\n\n"
                f"Publisher: {reference.get('publisher', 'Not recorded')}\n"
                f"Official link: {url}\n\n"
                f"Source policy: {category['source_policy']}. Metadata only; publication text is not hosted.\n"
                f"Seed needs_verification flag: {str(reference.get('needs_verification', False)).lower()}.\n"
                "The seed flag is not evidence of verification. Current status has not been live verified.\n\n"
                + DRAFT_NOTICE
            )
            items.append(LibraryItem(
                id=f"ref-{category_id.replace('_', '-')}-{identity}", title=reference["title"],
                category="reference", summary=reference.get("scope_note", category["name"]), content=content,
                sources=[SourceLink(title=reference["title"], url=url)],
                source_file=manifest_path, source_sha256=digest,
            ))
    template_dir = REPO_ROOT / "data/seed/system_templates"
    # The existing loader has no dependency on Settings or personal stores.
    templates = SystemTemplateCatalog.from_dir(template_dir)
    for template_id in TEMPLATE_IDS:
        relative_path = f"data/seed/system_templates/{template_id}.yaml"
        digest = source_digest(relative_path)
        detail = templates.get_detail(template_id)
        if detail is None:
            raise ValueError(f"Missing published template: {template_id}")
        lines = [
            f"# {detail.template_name}", "", detail.when_to_use or "", "",
            "Use placeholders only for operational details. Never enter real call signs, "
            "frequencies, challenge/password values, precise unit movements, or sensitive "
            "operational information into this template or an AI chat.",
            "", "## Draft scaffold", "",
        ]
        for section in detail.sections:
            lines.extend([f"### {section.heading}", "", section.scaffold.strip(), ""])
        lines.extend(["## References named in the source (confirm current status)", ""])
        lines.extend(f"- {reference}" for reference in detail.doctrine_refs)
        lines.extend(["", "## Guidance", ""])
        lines.extend(f"- {guidance}" for guidance in detail.guidance)
        lines.extend(["", DRAFT_NOTICE])
        items.append(LibraryItem(
            id=template_id, title=detail.template_name, category="template", summary=detail.one_liner or "Draft scaffold",
            content="\n".join(lines), sources=[SourceLink(title="Repository template source", url=REPO_URL + relative_path)],
            source_file=relative_path, source_sha256=digest,
        ))
    for prompt_id in PROMPT_IDS:
        relative_path = f"app/public_library/packs/{prompt_id}.md"
        digest = source_digest(relative_path)
        content = (REPO_ROOT / relative_path).read_text(encoding="utf-8").strip()
        items.append(LibraryItem(
            id=f"pack-{prompt_id}", title=content.splitlines()[0].removeprefix("# "), category="prompt_pack",
            summary=content.split("\n\n")[1].replace("\n", " "), content=content,
            sources=[SourceLink(title="Repository prompt source", url=REPO_URL + relative_path)],
            source_file=relative_path, source_sha256=digest,
        ))
    return CatalogSnapshot(items=sorted(items, key=lambda item: item.id))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the published snapshot differs from its sources.")
    args = parser.parse_args()
    serialized = json.dumps(build_snapshot().model_dump(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != serialized:
            raise SystemExit("Public catalog is stale. Review the allowlisted sources and rebuild the snapshot.")
        print("Public catalog matches its allowlisted sources.")
    else:
        OUTPUT.write_text(serialized, encoding="utf-8", newline="\n")
        print(f"Published {len(json.loads(serialized)['items'])} items to {OUTPUT}")


if __name__ == "__main__":
    main()
