from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.schemas.agents import Confidence
from app.schemas.source_state import VerifiedSourceStatus


class CivilEvidenceKind(StrEnum):
    sourced_observation = "sourced_observation"
    analytic_inference = "analytic_inference"
    planning_hypothesis = "planning_hypothesis"


class CivilNetworkNodeKind(StrEnum):
    organization = "organization"
    service = "service"
    forum = "forum"
    broad_group = "broad_group"
    public_role_holder = "public_role_holder"


class CivilNetworkRelationshipKind(StrEnum):
    coordination = "coordination"
    dependency = "dependency"
    influence = "influence"
    information_flow = "information_flow"
    authority_approval = "authority_approval"
    resource_support = "resource_support"
    legitimacy_trust = "legitimacy_trust"


class CivilNetworkReviewState(StrEnum):
    draft = "draft"
    reviewed = "reviewed"
    needs_review = "needs_review"


class CivilRelationshipDirection(StrEnum):
    directional = "directional"
    mutual = "mutual"


class CivilNetworkEvidence(BaseModel):
    """Cited, public or fictional-context support retained with a civil-network record."""

    source_id: str | None = Field(default=None, min_length=1, max_length=128)
    source_hash: str | None = Field(default=None, min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=500)
    url: str | None = Field(default=None, max_length=2_048)
    bibliographic_note: str | None = Field(default=None, max_length=2_000)
    publisher: str | None = Field(default=None, max_length=500)
    retrieved_at: date
    trust_status: VerifiedSourceStatus = VerifiedSourceStatus.needs_review
    excerpt: str = Field(min_length=1, max_length=5_000)
    confidence: Confidence = Confidence.low
    review_state: CivilNetworkReviewState = CivilNetworkReviewState.needs_review
    rationale: str | None = Field(default=None, max_length=2_000)


class CivilNetworkNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    kind: CivilNetworkNodeKind
    display_name: str = Field(min_length=1, max_length=500)
    public_role: str | None = Field(default=None, max_length=500)
    organization: str | None = Field(default=None, max_length=500)
    event_relevance: str | None = Field(default=None, max_length=2_000)
    evidence_kind: CivilEvidenceKind = CivilEvidenceKind.planning_hypothesis
    evidence: list[CivilNetworkEvidence] = Field(default_factory=list, max_length=50)
    confidence: Confidence = Confidence.low
    review_state: CivilNetworkReviewState = CivilNetworkReviewState.needs_review
    tags: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def require_public_role_holder_fields(self) -> CivilNetworkNode:
        if self.evidence_kind is CivilEvidenceKind.sourced_observation and not self.evidence:
            raise ValueError("Sourced observations require evidence.")
        if self.kind is not CivilNetworkNodeKind.public_role_holder:
            return self
        if not self.public_role or not self.organization or not self.event_relevance:
            raise ValueError("Public role-holders require public_role, organization, and event_relevance.")
        if not self.evidence:
            raise ValueError("Public role-holders require source/date evidence.")
        return self


class CivilNetworkRelationship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    from_node_id: str = Field(min_length=1, max_length=128)
    to_node_id: str = Field(min_length=1, max_length=128)
    kind: CivilNetworkRelationshipKind
    direction: CivilRelationshipDirection = CivilRelationshipDirection.directional
    evidence_kind: CivilEvidenceKind
    description: str = Field(min_length=1, max_length=2_000)
    evidence: list[CivilNetworkEvidence] = Field(default_factory=list, max_length=50)
    confidence: Confidence = Confidence.low
    review_state: CivilNetworkReviewState = CivilNetworkReviewState.needs_review
    notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def require_observation_evidence(self) -> CivilNetworkRelationship:
        if self.evidence_kind is CivilEvidenceKind.sourced_observation and not self.evidence:
            raise ValueError("Sourced observations require evidence.")
        return self


class CivilNetworkSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    network: CivilNetwork


class CivilNetwork(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=500)
    event_id: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=2_000)
    status: CivilNetworkReviewState = CivilNetworkReviewState.draft
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    nodes: list[CivilNetworkNode] = Field(default_factory=list, max_length=500)
    relationships: list[CivilNetworkRelationship] = Field(default_factory=list, max_length=2_000)
    snapshots: list[CivilNetworkSnapshot] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def require_existing_relationship_nodes(self) -> CivilNetwork:
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Civil-network node ids must be unique.")
        known_node_ids = set(node_ids)
        for relationship in self.relationships:
            if relationship.from_node_id not in known_node_ids or relationship.to_node_id not in known_node_ids:
                raise ValueError("Civil-network relationships must reference an existing node.")
        return self
