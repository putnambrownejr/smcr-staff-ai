from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input, should_limit_to_generic_response
from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus


class AgentContext(BaseModel):
    user_role: str | None = None
    unit_id: str | None = None
    request_is_training_or_fictional: bool = False
    extra: dict[str, object] = Field(default_factory=dict)


class Agent(ABC):
    metadata: AgentMetadata

    @abstractmethod
    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        raise NotImplementedError

    def _response(
        self,
        answer: str,
        input_text: str,
        follow_up_questions: list[str] | None = None,
        citations: list[str] | None = None,
        structured_citations: list[StructuredCitation] | None = None,
        source_trust: list[SourceTrustMarker] | None = None,
        confidence: Confidence = Confidence.low,
    ) -> AgentRunResponse:
        warnings = [*DEFAULT_WARNINGS, *detect_sensitive_input(input_text)]
        if should_limit_to_generic_response(input_text):
            answer = (
                "I cannot process classified, controlled, COMSEC, keying material, real frequencies, "
                "call signs, exact movements, or sensitive operational details. "
                "Here is a generic training-only checklist instead:\n\n"
                f"{answer}"
            )
            confidence = Confidence.low
        return AgentRunResponse(
            agent_id=self.metadata.id,
            answer=answer,
            citations=citations or [],
            structured_citations=structured_citations or [],
            source_trust=source_trust or _default_source_trust(self.metadata),
            warnings=warnings,
            human_review_required=self.metadata.required_human_review,
            confidence=confidence,
            follow_up_questions=follow_up_questions or [],
        )


class PlaceholderAgent(Agent):
    def __init__(
        self,
        metadata: AgentMetadata,
        checklist: list[str],
        follow_up_questions: list[str] | None = None,
    ) -> None:
        self.metadata = metadata
        self.checklist = checklist
        self.default_follow_up_questions = follow_up_questions or [
            "What public source or doctrine should this draft be grounded in?",
            "Is this for a fictional/training scenario or a real-world administrative workflow?",
        ]

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        lines = "\n".join(f"- {item}" for item in self.checklist)
        answer = (
            f"{self.metadata.name} placeholder response.\n\n"
            "Use this as a planning draft, not as an order or authoritative decision.\n\n"
            f"Suggested checklist:\n{lines}"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            follow_up_questions=self.default_follow_up_questions,
        )


def _default_source_trust(metadata: AgentMetadata) -> list[SourceTrustMarker]:
    if not metadata.citation_required:
        return []
    return [
        SourceTrustMarker(
            tracked_title=source,
            status=VerifiedSourceStatus.needs_review,
            notes="Review this source against the latest verified public reference before acting.",
        )
        for source in metadata.allowed_sources[:3]
    ]
