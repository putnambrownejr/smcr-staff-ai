from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BilletSourceKey(StrEnum):
    marforres_billets = "marforres_billets"
    manpower_dap = "manpower_dap"


class BilletSourceInfo(BaseModel):
    name: str
    url: str
    description: str
    warnings: list[str] = Field(default_factory=list)


class SmcrBillet(BaseModel):
    bic: str | None = None
    title: str
    unit: str | None = None
    location: str | None = None
    rank: str | None = None
    rank_min: str | None = None
    rank_max: str | None = None
    mos: str | None = None
    component: str = "SMCR"
    source_url: str | None = None
    notes: str | None = None


class BilletUserProfile(BaseModel):
    mos: str | None = Field(default=None, description="Current or desired MOS, for example 0602 or 0530.")
    rank: str | None = Field(default=None, description="Current rank/grade, for example Capt or O3.")
    desired_locations: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    willing_to_travel: bool = True


class BilletRecommendation(BaseModel):
    billet: SmcrBillet
    score: int
    match_reasons: list[str]
    warnings: list[str] = Field(default_factory=list)


class BilletSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: BilletUserProfile
    source_key: BilletSourceKey = BilletSourceKey.marforres_billets
    max_results: int = Field(default=10, ge=1, le=50)


class BilletSearchResponse(BaseModel):
    source: BilletSourceInfo
    discovered_links: list[str] = Field(default_factory=list)
    billets_seen: int
    recommendations: list[BilletRecommendation]
    warnings: list[str] = Field(default_factory=list)
