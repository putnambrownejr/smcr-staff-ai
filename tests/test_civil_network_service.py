import hashlib
from datetime import date
from pathlib import Path

import pytest

from app.schemas.agents import SourceSelection
from app.schemas.civil_network import (
    CivilEvidenceKind,
    CivilNetwork,
    CivilNetworkEvidence,
    CivilNetworkNode,
)
from app.schemas.source_library import SavedSource
from app.schemas.source_state import VerifiedSourceStatus
from app.services.agents.source_context import SourceEvidenceResolver
from app.services.rag.chunking import TextChunk
from app.services.source_library.store import SourceLibraryStore
from app.services.staff.civil_network_service import CivilNetworkService
from app.services.staff.civil_network_store import CivilNetworkStore


def test_current_selected_source_becomes_provenance(tmp_path: Path) -> None:
    service, source_id = _service_with_saved_source(tmp_path, VerifiedSourceStatus.current)
    network = _network_with_selected_evidence(source_id)

    saved = service.create_or_update(
        "owner", network, SourceSelection(source_ids=[source_id]), include_noncurrent=False
    )

    evidence = saved.nodes[0].evidence[0]
    assert evidence.source_hash == hashlib.sha256(source_id.encode()).hexdigest()
    assert evidence.trust_status is VerifiedSourceStatus.current
    assert evidence.publisher == "Example publisher"
    assert evidence.url == f"https://example.test/{source_id}"


def test_watch_source_requires_explicit_opt_in(tmp_path: Path) -> None:
    service, source_id = _service_with_saved_source(tmp_path, VerifiedSourceStatus.watch)

    with pytest.raises(ValueError, match="noncurrent"):
        service.create_or_update(
            "owner", _network_with_selected_evidence(source_id), SourceSelection(source_ids=[source_id]), False
        )


def test_manual_citation_requires_url_or_bibliographic_note(tmp_path: Path) -> None:
    service, _ = _service_with_saved_source(tmp_path, VerifiedSourceStatus.current)
    network = CivilNetwork(
        title="Flood exercise",
        event_id="flood-26",
        purpose="G-9 coordination",
        nodes=[
            CivilNetworkNode(
                kind="organization",
                display_name="County emergency management",
                evidence_kind=CivilEvidenceKind.sourced_observation,
                evidence=[
                    CivilNetworkEvidence(
                        title="County plan",
                        retrieved_at=date(2026, 7, 16),
                        excerpt="Coordinates support.",
                    )
                ],
            )
        ],
    )

    with pytest.raises(ValueError, match="manual citation"):
        service.create_or_update("owner", network, None, include_noncurrent=False)


def test_manual_citation_requires_explicit_confidence_and_review_state(tmp_path: Path) -> None:
    service, _ = _service_with_saved_source(tmp_path, VerifiedSourceStatus.current)
    network = CivilNetwork(
        title="Flood exercise",
        event_id="flood-26",
        purpose="G-9 coordination",
        nodes=[
            CivilNetworkNode(
                kind="organization",
                display_name="County emergency management",
                evidence_kind=CivilEvidenceKind.sourced_observation,
                evidence=[
                    CivilNetworkEvidence(
                        title="County plan",
                        url="https://example.test/plan",
                        retrieved_at=date(2026, 7, 16),
                        excerpt="Coordinates support.",
                    )
                ],
            )
        ],
    )

    with pytest.raises(ValueError, match="explicit confidence"):
        service.create_or_update("owner", network, None, include_noncurrent=False)


def test_sensitive_network_text_is_rejected(tmp_path: Path) -> None:
    service, _ = _service_with_saved_source(tmp_path, VerifiedSourceStatus.current)
    network = CivilNetwork(
        title="Flood exercise",
        event_id="flood-26",
        purpose="Current movement coordination",
    )

    with pytest.raises(ValueError, match="sensitive"):
        service.create_or_update("owner", network, None, include_noncurrent=False)


def _network_with_selected_evidence(source_id: str) -> CivilNetwork:
    return CivilNetwork(
        title="Flood exercise",
        event_id="flood-26",
        purpose="G-9 coordination",
        nodes=[
            CivilNetworkNode(
                kind="organization",
                display_name="County emergency management",
                evidence_kind=CivilEvidenceKind.sourced_observation,
                evidence=[
                    CivilNetworkEvidence(
                        source_id=source_id,
                        title="Placeholder selected source",
                        retrieved_at=date(2026, 7, 16),
                        excerpt="Coordinates support.",
                    )
                ],
            )
        ],
    )


def _service_with_saved_source(
    tmp_path: Path, trust_status: VerifiedSourceStatus
) -> tuple[CivilNetworkService, str]:
    source_id = "saved-source"
    source_store = SourceLibraryStore(tmp_path / "sources")
    text = "The county coordinates emergency support."
    source = SavedSource(
        source_id=source_id,
        user_key_digest="0" * 64,
        original_url=f"https://example.test/{source_id}",
        canonical_url=f"https://example.test/{source_id}",
        title="Reviewed emergency plan",
        publisher="Example publisher",
        media_type="text/plain",
        content_hash=hashlib.sha256(source_id.encode()).hexdigest(),
        byte_size=len(text),
        raw_content_path="",
        normalized_text_path="",
        chunks_path="",
        chunk_count=0,
        trust_status=trust_status,
    )
    source_store.save("owner", source, text.encode(), text, [TextChunk(chunk_index=0, text=text)])
    return (
        CivilNetworkService(CivilNetworkStore(tmp_path / "networks"), SourceEvidenceResolver(source_store)),
        source_id,
    )
