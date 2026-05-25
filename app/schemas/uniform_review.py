from pydantic import BaseModel, Field

from app.schemas.agents import StructuredCitation
from app.schemas.source_state import SourceTrustMarker


class UniformPhotoReviewResponse(BaseModel):
    photo_context_id: str
    filename: str
    uniform_type: str
    event_context: str | None = None
    visible_items: list[str] = Field(default_factory=list)
    review_posture: str
    summary_lines: list[str] = Field(default_factory=list)
    what_to_verify_in_image: list[str] = Field(default_factory=list)
    grooming_checks: list[str] = Field(default_factory=list)
    likely_issue_areas: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    source_trust: list[SourceTrustMarker] = Field(default_factory=list)
