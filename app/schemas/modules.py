from __future__ import annotations

from pydantic import BaseModel, Field


class ModuleManifest(BaseModel):
    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    author: str = ""
    version: str = ""


class ModuleFile(BaseModel):
    filename: str
    size_bytes: int
    content_type: str


class ModulePackSummary(BaseModel):
    pack_name: str
    manifest: ModuleManifest
    file_count: int
    supported_file_count: int


class ModulePackDetail(ModulePackSummary):
    files: list[ModuleFile]


class ModuleIngestResult(BaseModel):
    pack_name: str
    ingested: list[str]
    skipped: list[str]
    replaced: int
    message: str
