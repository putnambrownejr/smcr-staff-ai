from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, Relationship, SQLModel


class ClassificationLabel(StrEnum):
    unclassified = "UNCLASSIFIED"
    cui = "CUI"


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True, unique=True)
    title: str
    publication_type: str
    issuing_org: str | None = None
    url: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str | None = None
    effective_date: datetime | None = None
    classification_label: str = ClassificationLabel.unclassified.value
    cui_flag: bool = False
    source_hash: str | None = None
    chunks: list["DocumentChunk"] = Relationship(back_populates="document")


class DocumentChunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    document_id: int | None = Field(default=None, foreign_key="document.id")
    chunk_index: int
    text: str
    page_number: int | None = None
    paragraph_index: int | None = None
    metadata_json: str | None = None
    document: Document | None = Relationship(back_populates="chunks")


class MessageRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True)
    title: str
    link: str
    published_at: datetime | None = None
    summary: str | None = None
    tags_csv: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CalendarPlan(SQLModel, table=True):
    id: str = Field(primary_key=True)
    drill_date: datetime
    title: str
    tasks_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrgUnit(SQLModel, table=True):
    unit_id: str = Field(primary_key=True)
    name: str
    unit_type: str
    component: str
    location: str | None = None
    higher_headquarters_id: str | None = Field(default=None, foreign_key="orgunit.unit_id")
    example_data: bool = True
