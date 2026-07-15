from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.billets import BilletRecommendation, BilletUserProfile, SmcrBillet
from app.schemas.opportunities import (
    ManualOpportunityRequest,
    OpportunityRecommendation,
    OpportunityRecord,
    OpportunityType,
)
from app.services.billets.recommender import recommend_billets

DEFAULT_OPPORTUNITY_WARNINGS = [
    "Opportunity data is advisory only and may change quickly. Verify through official channels.",
    "Tracked opportunities do not determine eligibility, selection, or approval.",
]


class OpportunityTracker:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def track(self, opportunities: Sequence[ManualOpportunityRequest]) -> Sequence[OpportunityRecord]:
        tracked = [self._record_from_manual(opportunity) for opportunity in opportunities]
        for record in tracked:
            self._path(record.opportunity_id).write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return tracked

    def list(self, opportunity_type: OpportunityType | None = None) -> Sequence[OpportunityRecord]:
        records = [
            OpportunityRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.root_dir.glob("*.json"))
        ]
        if opportunity_type is not None:
            records = [record for record in records if record.opportunity_type == opportunity_type]
        return sorted(
            records,
            key=lambda record: (
                record.due_date or (record.tracked_at or record.detected_at).date(),
                record.title,
            ),
        )

    def recommend(
        self,
        profile: BilletUserProfile,
        opportunities: Sequence[ManualOpportunityRequest],
        max_results: int = 10,
    ) -> Sequence[OpportunityRecommendation]:
        billets = [_as_billet(opportunity) for opportunity in opportunities]
        billet_recommendations = recommend_billets(billets, profile, max_results=max_results)
        return [_from_billet_recommendation(recommendation) for recommendation in billet_recommendations]

    def _record_from_manual(self, opportunity: ManualOpportunityRequest) -> OpportunityRecord:
        opportunity_id = _opportunity_id(opportunity)
        return OpportunityRecord(
            opportunity_id=opportunity_id,
            title=opportunity.title,
            opportunity_type=opportunity.opportunity_type,
            unit=opportunity.unit,
            location=opportunity.location,
            mos=opportunity.mos,
            rank=opportunity.rank,
            source_url=opportunity.source_url,
            source_name=opportunity.source_name,
            description=opportunity.description,
            notes=opportunity.notes,
            due_date=opportunity.due_date,
            tracked=True,
            tracked_at=datetime.now(UTC),
            warnings=DEFAULT_OPPORTUNITY_WARNINGS,
        )

    def _path(self, opportunity_id: str) -> Path:
        safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in opportunity_id)
        return self.root_dir / f"{safe_id}.json"


def _opportunity_id(opportunity: ManualOpportunityRequest) -> str:
    seed = "|".join(
        [
            opportunity.opportunity_type.value,
            opportunity.title,
            opportunity.unit or "",
            opportunity.location or "",
            opportunity.mos or "",
            opportunity.rank or "",
            opportunity.source_url or "",
        ]
    )
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _as_billet(opportunity: ManualOpportunityRequest) -> SmcrBillet:
    component = "ADOS" if opportunity.opportunity_type == OpportunityType.ados else "SMCR"
    return SmcrBillet(
        title=opportunity.title,
        unit=opportunity.unit,
        location=opportunity.location,
        rank=opportunity.rank,
        mos=opportunity.mos,
        component=component,
        source_url=opportunity.source_url,
        notes=" ".join(item for item in [opportunity.description, opportunity.notes, opportunity.source_name] if item),
    )


def _from_billet_recommendation(recommendation: BilletRecommendation) -> OpportunityRecommendation:
    billet = recommendation.billet
    opportunity_type = OpportunityType.ados if (billet.component or "").upper() == "ADOS" else OpportunityType.smcr
    return OpportunityRecommendation(
        opportunity=OpportunityRecord(
            opportunity_id=hashlib.sha256(
                f"{opportunity_type.value}|{billet.title}|{billet.unit or ''}|{billet.location or ''}".encode()
            ).hexdigest()[:20],
            title=billet.title,
            opportunity_type=opportunity_type,
            unit=billet.unit,
            location=billet.location,
            mos=billet.mos,
            rank=billet.rank,
            source_url=billet.source_url,
            description=billet.notes,
            warnings=DEFAULT_OPPORTUNITY_WARNINGS,
            tracked=False,
        ),
        score=recommendation.score,
        match_reasons=recommendation.match_reasons,
        warnings=[*DEFAULT_OPPORTUNITY_WARNINGS, *recommendation.warnings],
    )
