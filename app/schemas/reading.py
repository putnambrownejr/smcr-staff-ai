from pydantic import BaseModel, Field


class ReadingListSource(BaseModel):
    name: str
    url: str
    source_type: str
    notes: str | None = None


class ReadingListBook(BaseModel):
    slug: str
    title: str
    author: str
    categories: list[str] = Field(default_factory=list)
    list_years: list[str] = Field(default_factory=list)
    open_source_available: bool = False
    public_domain: bool = False
    source_urls: list[str] = Field(default_factory=list)
    summary: str
    key_themes: list[str] = Field(default_factory=list)
    discussion_prompts: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)


class ReadingListCatalog(BaseModel):
    notice: str
    sources: list[ReadingListSource]
    books: list[ReadingListBook]


class ReadingListBookSummary(BaseModel):
    book: ReadingListBook
    citations: list[str]
    warnings: list[str] = Field(default_factory=list)
