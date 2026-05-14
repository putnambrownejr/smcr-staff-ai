from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl


class SourceVerificationStatus(StrEnum):
    verified_exact = "verified_exact"
    tag_page_only = "tag_page_only"
    placeholder = "placeholder"
    do_not_ingest = "do_not_ingest"


class SourceRef(BaseModel):
    title: str
    url: HttpUrl
    source_id: str | None = None
    publication_number: str | None = None
    issuing_org: str | None = None
    version: str | None = None
    effective_date: str | None = None
    retrieval_date: str | None = None
    source_hash: str | None = None
    classification_label: str = "UNCLASSIFIED"
    cui_flag: bool = False
    verification_status: SourceVerificationStatus = SourceVerificationStatus.placeholder
    copyright_policy: str = "metadata_only"
    notes: str | None = None


class DoctrineCategory(BaseModel):
    id: str
    name: str
    publication_families: list[str]
    source_policy: str
    classification_label: str = "UNCLASSIFIED"
    cui_flag: bool = False
    source_refs: list[SourceRef] = Field(default_factory=list)


class DoctrineManifest(BaseModel):
    notice: str
    categories: list[DoctrineCategory]
    planning_refs: list[dict[str, Any]] = Field(default_factory=list)


class ManifestValidationResult(BaseModel):
    category_count: int
    source_ref_count: int
    placeholder_count: int
    tag_page_count: int
    do_not_ingest_count: int
    warnings: list[str] = Field(default_factory=list)
    blocking_errors: list[str] = Field(default_factory=list)


def load_doctrine_manifest(path: str | Path) -> DoctrineManifest:
    with open(path, encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return DoctrineManifest.model_validate(payload)


def validate_manifest(path: str | Path) -> ManifestValidationResult:
    manifest = load_doctrine_manifest(path)
    refs = [ref for category in manifest.categories for ref in category.source_refs]
    warnings: list[str] = []
    for category in manifest.categories:
        if not category.source_refs:
            warnings.append(f"Category {category.id} has no source_refs yet.")
    for ref in refs:
        if ref.verification_status != SourceVerificationStatus.verified_exact:
            warnings.append(f"Source {ref.title} is marked {ref.verification_status.value}.")
        if ref.verification_status == SourceVerificationStatus.do_not_ingest:
            warnings.append(f"Source {ref.title} must not be ingested.")
        if ref.classification_label.upper() != "UNCLASSIFIED" or ref.cui_flag:
            warnings.append(f"Source {ref.title} is not eligible for public prototype ingestion.")
    blocking_errors = [
        warning
        for warning in warnings
        if "must not be ingested" in warning or "not eligible for public prototype ingestion" in warning
    ]
    return ManifestValidationResult(
        category_count=len(manifest.categories),
        source_ref_count=len(refs),
        placeholder_count=sum(ref.verification_status == SourceVerificationStatus.placeholder for ref in refs),
        tag_page_count=sum(ref.verification_status == SourceVerificationStatus.tag_page_only for ref in refs),
        do_not_ingest_count=sum(ref.verification_status == SourceVerificationStatus.do_not_ingest for ref in refs),
        warnings=warnings,
        blocking_errors=blocking_errors,
    )
