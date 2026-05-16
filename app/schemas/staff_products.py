from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import Confidence, StructuredCitation


class StaffProductType(StrEnum):
    opord = "opord"
    warno = "warno"
    frago = "frago"
    conop = "conop"
    sitrep = "sitrep"
    aar = "aar"
    naval_letter = "naval_letter"
    memorandum = "memorandum"
    endorsement = "endorsement"


class StaffProductDraftRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_type": "opord",
                "topic": "Training-only drill weekend field exercise",
                "audience": "Company staff",
                "facts": ["Timeline is tentative", "Scenario is fictional and training-only"],
                "training_or_fictional": True,
            }
        }
    )
    product_type: StaffProductType
    topic: str = Field(min_length=1)
    audience: str | None = None
    echelon: str | None = None
    preferred_format: str | None = None
    facts: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    training_or_fictional: bool = True
    include_review_checklist: bool = True


class StaffProductSection(BaseModel):
    heading: str
    prompts: list[str]


class StaffProductDraftResponse(BaseModel):
    product_type: StaffProductType
    title: str
    sections: list[StaffProductSection]
    formatting_notes: list[str] = Field(default_factory=list)
    review_checklist: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
