from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.external_processing import ExternalProcessingApproval
from app.schemas.source_state import SourceTrustMarker


class Confidence(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ScenarioOutputStatus(StrEnum):
    not_applicable = "not_applicable"
    template_only = "template_only"
    validated = "validated"
    invalid = "invalid"


class AgentMetadata(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    # Curated grouping for presentation (dashboard AI page). `domain` stays the
    # agent's own fine-grained self-description; `category` buckets agents into a
    # handful of human-facing groups (assigned in the registry, not per-builder).
    category: str = "Other Advisors"
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


class SourceSelection(BaseModel):
    """A bounded request to use locally retained Source Library evidence."""

    source_ids: list[str] = Field(default_factory=list, max_length=20)
    query: str | None = Field(default=None, max_length=500)
    limit: int = Field(default=6, ge=1, le=20)
    include_noncurrent: bool = False


class ResolvedSourceEvidence(BaseModel):
    """Normalized local evidence and its trust markers for an agent run."""

    items: list[dict[str, str]] = Field(default_factory=list)
    source_trust: list[SourceTrustMarker] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
    source_selection: SourceSelection | None = None
    external_processing_approval: ExternalProcessingApproval | None = None


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
    scenario_output: dict[str, Any] | None = None
    scenario_output_status: ScenarioOutputStatus = ScenarioOutputStatus.not_applicable
