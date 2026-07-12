from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.schemas.prompt_packs import PromptPackCatalogResponse, PromptPackEntry

router = APIRouter(prefix="/prompt-packs", tags=["prompt packs"])
REPO_ROOT = Path(__file__).resolve().parents[3]
PACKS_DIR = REPO_ROOT / "prompt-packs"


@router.get("", response_model=PromptPackCatalogResponse)
def list_prompt_packs() -> PromptPackCatalogResponse:
    packs = _load_prompt_packs()
    return PromptPackCatalogResponse(packs=list(packs), total=len(packs))


@lru_cache
def _load_prompt_packs() -> tuple[PromptPackEntry, ...]:
    if not PACKS_DIR.exists():
        return ()
    entries: list[PromptPackEntry] = []
    for path in sorted(PACKS_DIR.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        title = next((line.lstrip("#").strip() for line in lines if line.startswith("# ")), path.stem)
        summary = next(
            (line.strip() for line in lines[1:] if line.strip() and not line.startswith("#")),
            "",
        )
        entries.append(PromptPackEntry(slug=path.stem, title=title, summary=summary, content=content))
    return tuple(entries)
