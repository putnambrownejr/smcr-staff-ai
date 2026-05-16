from __future__ import annotations

from pathlib import Path

from app.schemas.source_verification import (
    SourceVerificationFinding,
    SourceVerificationRequest,
    SourceVerificationResponse,
)
from app.schemas.sources import (
    ManifestValidationResult,
    SourceRef,
    SourceVerificationStatus,
    validate_manifest,
)


class SourceVerifier:
    def verify(self, request: SourceVerificationRequest) -> SourceVerificationResponse:
        manifest_validation = None
        findings: list[SourceVerificationFinding] = []
        warnings: list[str] = []
        if request.manifest_path:
            manifest_path = resolve_repo_local_path(request.manifest_path)
            if not manifest_path.exists():
                raise FileNotFoundError(f"Manifest not found: {manifest_path}")
            manifest_validation = validate_manifest(manifest_path)
            warnings.extend(manifest_validation.warnings)
        findings.extend(_findings_for_refs(request.refs))
        warnings.extend(item for finding in findings for item in finding.warnings)
        return SourceVerificationResponse(
            manifest_validation=manifest_validation,
            findings=findings,
            summary_lines=_summary_lines(manifest_validation, findings),
        warnings=sorted(set(warnings)),
    )


def resolve_repo_local_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        raise FileNotFoundError("Absolute local paths are not allowed for source verification in this prototype.")

    repo_root = Path(__file__).resolve().parents[3]
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise FileNotFoundError("Local paths must stay within the repository workspace.") from exc
    return resolved


def _findings_for_refs(refs: list[SourceRef]) -> list[SourceVerificationFinding]:
    return [
        SourceVerificationFinding(
            title=ref.title,
            verification_status=ref.verification_status.value,
            classification_label=ref.classification_label,
            eligible_for_public_prototype=ref.classification_label.upper() == "UNCLASSIFIED" and not ref.cui_flag,
            warnings=_warnings_for_ref(ref),
        )
        for ref in refs
    ]


def _warnings_for_ref(ref: SourceRef) -> list[str]:
    warnings: list[str] = []
    if ref.verification_status != SourceVerificationStatus.verified_exact:
        warnings.append(f"{ref.title} is marked {ref.verification_status.value}.")
    if ref.classification_label.upper() != "UNCLASSIFIED" or ref.cui_flag:
        warnings.append(f"{ref.title} is not eligible for this public prototype.")
    if "mcpel" in str(ref.url).lower() and ref.verification_status == SourceVerificationStatus.tag_page_only:
        warnings.append(f"{ref.title} still needs an exact MCPEL item-page verification step.")
    return warnings


def _summary_lines(
    manifest_validation: ManifestValidationResult | None,
    findings: list[SourceVerificationFinding],
) -> list[str]:
    lines: list[str] = []
    if manifest_validation is not None:
        lines.append(f"Manifest includes {manifest_validation.source_ref_count} source reference(s).")
        if manifest_validation.placeholder_count:
            lines.append(f"{manifest_validation.placeholder_count} source reference(s) remain placeholder-only.")
        if manifest_validation.tag_page_count:
            lines.append(
                f"{manifest_validation.tag_page_count} source reference(s) are tag-page-only "
                "and need exact verification."
            )
    if findings:
        unverified = sum(finding.verification_status != "verified_exact" for finding in findings)
        if unverified:
            lines.append(f"{unverified} provided source reference(s) still need stronger verification.")
    return lines
