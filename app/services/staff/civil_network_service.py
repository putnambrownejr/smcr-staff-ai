"""Evidence normalization and safety checks for civil-network writes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from app.core.security import detect_sensitive_input
from app.schemas.agents import SourceSelection
from app.schemas.civil_network import CivilNetwork, CivilNetworkEvidence, CivilNetworkSnapshot
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.staff.civil_network_store import CivilNetworkStore


class CivilNetworkService:
    """Persist owner-scoped networks using only cited manual or saved local evidence."""

    def __init__(self, store: CivilNetworkStore, source_evidence_resolver: SourceEvidenceResolver) -> None:
        self._store = store
        self._source_evidence_resolver = source_evidence_resolver

    def create_or_update(
        self,
        user_key: str,
        network: CivilNetwork,
        source_selection: SourceSelection | None,
        include_noncurrent: bool,
    ) -> CivilNetwork:
        """Validate, locally resolve selected source records, and save a network.

        Source selection only reads Source Library content through its existing,
        owner-scoped resolver. It never fetches a URL or infers a relationship.
        """
        if network.snapshots:
            raise ValueError("Snapshots are created only through the snapshot endpoint.")
        self._reject_sensitive_text(network)
        resolved_sources = self._resolve_sources(user_key, source_selection, include_noncurrent)
        normalized = self._normalize_network_evidence(network, resolved_sources)
        try:
            existing = self._store.get(user_key, normalized.id)
        except KeyError:
            return self._store.create(user_key, normalized)
        return self._store.save(
            user_key,
            normalized.model_copy(update={"snapshots": existing.snapshots}, deep=True),
        )

    def snapshot(self, user_key: str, network_id: str, label: str) -> CivilNetworkSnapshot:
        self._reject_sensitive_text(label)
        return self._store.snapshot(user_key, network_id, label)

    def _resolve_sources(
        self, user_key: str, source_selection: SourceSelection | None, include_noncurrent: bool
    ) -> dict[str, dict[str, str]]:
        if source_selection is None:
            return {}
        selection = source_selection.model_copy(
            update={"include_noncurrent": include_noncurrent or source_selection.include_noncurrent}
        )
        resolved = self._source_evidence_resolver.resolve(user_key, selection)
        return {
            item["chunk_id"].partition(":")[0]: item
            for item in resolved.items
            if item.get("chunk_id") and item.get("source_hash")
        }

    def _normalize_network_evidence(
        self, network: CivilNetwork, resolved_sources: dict[str, dict[str, str]]
    ) -> CivilNetwork:
        nodes = [
            node.model_copy(update={"evidence": self._normalize_evidence(node.evidence, resolved_sources)}, deep=True)
            for node in network.nodes
        ]
        relationships = [
            relationship.model_copy(
                update={"evidence": self._normalize_evidence(relationship.evidence, resolved_sources)}, deep=True
            )
            for relationship in network.relationships
        ]
        return network.model_copy(update={"nodes": nodes, "relationships": relationships}, deep=True)

    def _normalize_evidence(
        self, evidence_records: Iterable[CivilNetworkEvidence], resolved_sources: dict[str, dict[str, str]]
    ) -> list[CivilNetworkEvidence]:
        normalized: list[CivilNetworkEvidence] = []
        for evidence in evidence_records:
            if evidence.source_id is None:
                self._require_manual_citation(evidence)
                normalized.append(evidence)
                continue
            source = resolved_sources.get(evidence.source_id)
            if source is None:
                raise ValueError(
                    "Selected source evidence is unavailable or noncurrent; explicitly opt in to noncurrent sources."
                )
            normalized.append(
                evidence.model_copy(
                    update={
                        "source_hash": source["source_hash"],
                        "title": source["title"],
                        "url": source["url"],
                        "publisher": source["publisher"] or None,
                        "retrieved_at": date.fromisoformat(source["retrieved_at"][:10]),
                        "trust_status": VerifiedSourceStatus(source["trust_status"]),
                        "excerpt": source["excerpt"],
                    }
                )
            )
        return normalized

    @staticmethod
    def _require_manual_citation(evidence: CivilNetworkEvidence) -> None:
        if not evidence.url and not evidence.bibliographic_note:
            raise ValueError("A manual citation requires a URL or bibliographic note.")
        required_explicit_fields = {"confidence", "review_state"}
        if not required_explicit_fields.issubset(evidence.model_fields_set):
            raise ValueError("A manual citation requires explicit confidence and review_state.")

    @staticmethod
    def _reject_sensitive_text(value: CivilNetwork | str) -> None:
        text = value if isinstance(value, str) else _all_text(value.model_dump(mode="json"))
        if detect_sensitive_input(text):
            raise ValueError("sensitive or personal information is not permitted in civil networks.")


def _all_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_all_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_all_text(item) for item in value)
    return ""
