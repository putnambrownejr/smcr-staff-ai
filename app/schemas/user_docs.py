from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class UserDocCategory(StrEnum):
    notebook = "notebook"
    fitreps = "fitreps"
    generations = "generations"


class UserDocEntry(BaseModel):
    id: str
    category: UserDocCategory
    title: str
    body: str = ""
    fields: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserDocCreateRequest(BaseModel):
    title: str
    body: str = ""
    fields: dict[str, Any] = Field(default_factory=dict)


class UserDocUpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    fields: dict[str, Any] | None = None


class SaveToProjectRequest(BaseModel):
    project: str


class SaveToProjectResponse(BaseModel):
    path: str
    message: str
