from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source_state import SourceTrustMarker


class Confidence(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class AgentMetadata(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    intended_users: list[str]
    allowed_sources: list[str]
    disallowed_inputs: list[str]
    system_prompt: str
    required_human_review: bool = True
    citation_required: bool = True


class StructuredCitation(BaseModel):
    title: str
    url: str | None = None
    publisher: str | None = None
    retrieved_at: str | None = None
    source_hash: str | None = None
    document_version: str | None = None
    effective_date: str | None = None
    page: int | None = None
    paragraph: int | None = None
    chunk_id: str | None = None
    confidence: Confidence = Confidence.low
    notes: str | None = None


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input": "Build a training-only PACE checklist for a drill weekend.",
                "context": {"request_is_training_or_fictional": True, "user_role": "CommO"},
            }
        }
    )
    input: str = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    agent_id: str
    answer: str
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    source_trust: list[SourceTrustMarker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    confidence: Confidence = Confidence.low
    follow_up_questions: list[str] = Field(default_factory=list)
