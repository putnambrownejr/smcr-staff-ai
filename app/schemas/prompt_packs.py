from pydantic import BaseModel


class PromptPackEntry(BaseModel):
    slug: str
    title: str
    summary: str
    content: str


class PromptPackCatalogResponse(BaseModel):
    packs: list[PromptPackEntry]
    total: int
