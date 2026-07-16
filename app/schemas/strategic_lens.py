"""Shared, non-tactical contract for strategic-lens exercise analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class StrategicLensMode(StrEnum):
    fictional = "fictional"
    public_source = "public_source"


class StrategicPostureCard(StrEnum):
    """Neutral strategic patterns, not descriptions of a people or nation."""

    indirect_leverage = "indirect_leverage"
    legitimacy_first = "legitimacy_first"
    threshold_sensitive = "threshold_sensitive"
    systems_friction = "systems_friction"
    information_contest = "information_contest"
    partner_reliance = "partner_reliance"
    short_term_risk = "short_term_risk"
    force_preservation = "force_preservation"
    asymmetric_systems_effect = "asymmetric_systems_effect"


class StrategicLensRequest(BaseModel):
    mode: StrategicLensMode
    actor_name: str = Field(min_length=1, max_length=160)
    fictional_actor_confirmed: bool = False
    posture_cards: list[StrategicPostureCard] = Field(default_factory=list)


class StrategicLensEvidenceProvenance(BaseModel):
    """Retained metadata for an attributed local-source observation."""

    title: str
    url: str | None = None
    publisher: str | None = None
    retrieved_at: str | None = None
    source_hash: str
    trust_status: str


class StrategicLensOutput(BaseModel):
    mode: StrategicLensMode
    actor_name: str
    strategic_objective: list[str] = Field(default_factory=list)
    theory_of_advantage: list[str] = Field(default_factory=list)
    risk_and_escalation_posture: list[str] = Field(default_factory=list)
    force_employment_preference: list[str] = Field(default_factory=list)
    information_posture: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    observable_indicators: list[str] = Field(default_factory=list)
    competing_interpretation: str = ""
    discriminator: str = ""
    evidence_observations: list[str] = Field(default_factory=list)
    evidence_provenance: list[StrategicLensEvidenceProvenance] = Field(default_factory=list)
    source_hashes: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
