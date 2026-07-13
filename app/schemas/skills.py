from pydantic import BaseModel


class SkillEntry(BaseModel):
    name: str
    description: str
    # "staff" (reserve staff work) or "development" (building the repo itself),
    # from the subsection the skill is listed under in skills/README.md.
    audience: str = "staff"


class SkillCatalogResponse(BaseModel):
    skills: list[SkillEntry]
    total: int
