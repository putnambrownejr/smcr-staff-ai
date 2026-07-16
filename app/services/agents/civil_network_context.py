"""Read-only civil-network snapshot rendering for planning agents."""

from __future__ import annotations

from app.schemas.civil_network import (
    CivilEvidenceKind,
    CivilNetworkEvidence,
    CivilNetworkSnapshot,
)
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus
from app.services.agents.base import AgentContext


def civil_network_snapshot(context: AgentContext) -> CivilNetworkSnapshot | None:
    """Validate the supplied snapshot without changing its saved content."""
    raw = context.extra.get("civil_network_snapshot")
    if raw is None:
        return None
    return raw if isinstance(raw, CivilNetworkSnapshot) else CivilNetworkSnapshot.model_validate(raw)


def civil_network_sections(snapshot: CivilNetworkSnapshot | None) -> str:
    if snapshot is None:
        return ""
    observations: list[str] = []
    inferences: list[str] = []
    hypotheses: list[str] = []
    warnings: list[str] = []
    for node in snapshot.network.nodes:
        _append_record(
            node.display_name, node.evidence_kind, node.evidence, observations, inferences, hypotheses, warnings
        )
    for edge in snapshot.network.relationships:
        label = f"{edge.from_node_id} → {edge.to_node_id} ({edge.kind.value}): {edge.description}"
        _append_record(label, edge.evidence_kind, edge.evidence, observations, inferences, hypotheses, warnings)
    return (
        f"Civil-network snapshot (read-only): {snapshot.label} — event {snapshot.network.event_id}.\n\n"
        f"Sourced observations:\n{_lines(observations, 'No sourced observations in the snapshot.')}\n\n"
        f"Analytic inferences:\n{_lines(inferences, 'No analytic inferences in the snapshot.')}\n\n"
        f"Planning hypotheses:\n{_lines(hypotheses, 'No planning hypotheses in the snapshot.')}\n\n"
        f"Provenance and warnings:\n{_lines(warnings, 'No noncurrent-source warnings in the snapshot.')}\n\n"
    )


def civil_network_source_trust(snapshot: CivilNetworkSnapshot | None) -> list[SourceTrustMarker]:
    if snapshot is None:
        return []
    markers: list[SourceTrustMarker] = []
    for evidence in _all_evidence(snapshot):
        markers.append(
            SourceTrustMarker(
                tracked_title=evidence.title,
                status=evidence.trust_status,
                verification_source_url=evidence.url,
                notes="Civil-network snapshot evidence; verify currency and applicability before acting.",
            )
        )
    return markers


def _append_record(
    label: str,
    kind: CivilEvidenceKind,
    evidence: list[CivilNetworkEvidence],
    observations: list[str],
    inferences: list[str],
    hypotheses: list[str],
    warnings: list[str],
) -> None:
    provenance = "; ".join(_provenance(item) for item in evidence) or "no cited evidence"
    rendered = f"{label} [provenance: {provenance}]"
    if kind is CivilEvidenceKind.sourced_observation:
        observations.append(rendered)
    elif kind is CivilEvidenceKind.analytic_inference:
        inferences.append(rendered)
    else:
        hypotheses.append(rendered)
    for item in evidence:
        if item.trust_status is not VerifiedSourceStatus.current:
            warnings.append(
                f"{item.title}: trust status is {item.trust_status.value}; confirm before relying on this record."
            )


def _all_evidence(snapshot: CivilNetworkSnapshot) -> list[CivilNetworkEvidence]:
    return [
        *(evidence for node in snapshot.network.nodes for evidence in node.evidence),
        *(evidence for relationship in snapshot.network.relationships for evidence in relationship.evidence),
    ]


def _provenance(evidence: CivilNetworkEvidence) -> str:
    source = evidence.url or evidence.bibliographic_note or "citation note missing"
    return f"{evidence.title}; {source}; retrieved {evidence.retrieved_at}; trust {evidence.trust_status.value}"


def _lines(items: list[str], fallback: str) -> str:
    return "\n".join(f"- {item}" for item in items) if items else f"- {fallback}"
