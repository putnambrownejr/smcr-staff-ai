from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import Confidence, StructuredCitation


class PersonnelProductType(StrEnum):
    fitrep_planning = "fitrep_planning"
    fitrep_bullets = "fitrep_bullets"
    award_package = "award_package"
    routing_package = "routing_package"


class PersonnelProductRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_type": "fitrep_planning",
                "title": "Annual FitRep prep",
                "subject_name": "Capt Example",
                "occasion": "Annual",
                "role": "MRO",
                "suspense_date": "2026-06-30",
                "facts": ["Served as battalion CommO during AT planning cycle"],
                "achievements": ["Built drill communications battle rhythm tracker"],
                "constraints": ["Do not include final comparative marks"],
                "routing_chain": ["MRO", "RS", "RO"],
                "document_references": ["Current draft support form", "Billet accomplishment tracker"],
            }
        }
    )

    product_type: PersonnelProductType
    title: str
    subject_name: str | None = None
    occasion: str | None = None
    role: str | None = None
    suspense_date: date | None = None
    facts: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    routing_chain: list[str] = Field(default_factory=list)
    document_references: list[str] = Field(default_factory=list)


class PersonnelDraftSection(BaseModel):
    heading: str
    prompts: list[str] = Field(default_factory=list)


class PersonnelProductResponse(BaseModel):
    product_type: PersonnelProductType
    title: str
    summary: list[str] = Field(default_factory=list)
    sections: list[PersonnelDraftSection] = Field(default_factory=list)
    routing_steps: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    review_points: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
