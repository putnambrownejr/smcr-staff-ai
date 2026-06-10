from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.skills import SkillCatalogResponse, SkillEntry

router = APIRouter(prefix="/skills", tags=["skills"])
REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_README = REPO_ROOT / "skills" / "README.md"


@router.get("", response_model=SkillCatalogResponse)
def list_skills() -> SkillCatalogResponse:
    return SkillCatalogResponse(skills=_load_skill_catalog(), total=len(_load_skill_catalog()))


@lru_cache
def _load_skill_catalog() -> list[SkillEntry]:
    if not SKILL_README.exists():
        raise HTTPException(status_code=404, detail="Skill catalog README not found.")
    lines = SKILL_README.read_text(encoding="utf-8").splitlines()
    skills: list[SkillEntry] = []
    in_section = False
    current_name: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if line == "## Available Skills":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        if line.startswith("- `") and "`" in line[3:]:
            current_name = line.split("`", 2)[1]
            continue
        if current_name and line.startswith("- "):
            skills.append(SkillEntry(name=current_name, description=line[2:].strip()))
            current_name = None
    return skills
