from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agents import Confidence, StructuredCitation


class PersonnelProductType(StrEnum):
    fitrep_planning = "fitrep_planning"
    fitrep_bullets = "fitrep_bullets"
    award_package = "award_package"
    routing_package = "routing_package"


class CorrespondenceFormatType(StrEnum):
    naval_letter = "naval_letter"
    memorandum = "memorandum"
    endorsement = "endorsement"
    routing_package = "routing_package"
    point_paper = "point_paper"
    professional_email = "professional_email"


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


class CorrespondenceConversionRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "format_type": "naval_letter",
                "title": "Request for drill travel support",
                "purpose": "Request travel support for drill attendance.",
                "audience": "Battalion S-1",
                "source_text": (
                    "Need a short formal request asking for travel support for reserve "
                    "drill attendance next month."
                ),
                "references": ["Current orders", "Local travel guidance"],
                "enclosures": ["Orders", "Travel estimate"],
                "constraints": ["Keep it brief", "Use advisory placeholders only"],
            }
        }
    )

    format_type: CorrespondenceFormatType
    title: str
    purpose: str
    audience: str | None = None
    source_text: str = Field(min_length=1)
    references: list[str] = Field(default_factory=list)
    enclosures: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class CorrespondenceSection(BaseModel):
    heading: str
    lines: list[str] = Field(default_factory=list)


class CorrespondenceConversionResponse(BaseModel):
    format_type: CorrespondenceFormatType
    title: str
    summary: list[str] = Field(default_factory=list)
    required_headers: list[str] = Field(default_factory=list)
    sections: list[CorrespondenceSection] = Field(default_factory=list)
    routing_notes: list[str] = Field(default_factory=list)
    review_points: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    structured_citations: list[StructuredCitation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
