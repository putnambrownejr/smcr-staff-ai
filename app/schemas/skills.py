from pydantic import BaseModel


class SkillEntry(BaseModel):
    name: str
    description: str


class SkillCatalogResponse(BaseModel):
    skills: list[SkillEntry]
    total: int
