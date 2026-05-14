import hashlib

from app.schemas.ingestion import MessageRecord
from app.schemas.source_updates import DocumentationUpdateCandidate, DocumentationUpdateScanResult, UpdateConfidence

DOCUMENT_UPDATE_KEYWORDS: tuple[str, ...] = (
    "revision",
    "revised",
    "change",
    "update",
    "updated",
    "publication",
    "published",
    "effective",
    "cancel",
    "canceled",
    "cancelled",
    "supersede",
    "superseded",
    "incorporated",
    "mcpel",
    "manual",
    "order",
    "bulletin",
)

TRACKED_SOURCE_TERMS: dict[str, tuple[str, ...]] = {
    "MCRAMM": ("mcramm", "1001r.1", "1001r1"),
    "Uniform Regulations": ("uniform", "1020.34"),
    "PES / FitRep": ("pes", "fitrep", "1610.7"),
    "Correspondence Manual": ("5216.20", "5216.5", "correspondence manual", "navy correspondence"),
    "MCDP 1 Warfighting": ("mcdp 1", "warfighting"),
    "MCDP 1-3 Tactics": ("mcdp 1-3", "tactics"),
    "MCDP 8 Information": ("mcdp 8", "information"),
    "ORM / Safety": ("orm", "risk management", "5100.29", "safety"),
}


class DocumentUpdateMonitor:
    def scan_maradmin_records(self, records: list[MessageRecord]) -> DocumentationUpdateScanResult:
        candidates: list[DocumentationUpdateCandidate] = []
        for record in records:
            text = f"{record.title} {record.summary or ''}".lower()
            change_signals = [keyword for keyword in DOCUMENT_UPDATE_KEYWORDS if keyword in text]
            if not change_signals:
                continue
            for tracked_title, terms in TRACKED_SOURCE_TERMS.items():
                matched_terms = [term for term in terms if term in text]
                if not matched_terms:
                    continue
                candidates.append(
                    DocumentationUpdateCandidate(
                        candidate_id=_candidate_id(record, tracked_title),
                        tracked_title=tracked_title,
                        trigger_type="maradmin",
                        trigger_source_id=record.source_id,
                        trigger_url=record.canonical_url,
                        matched_terms=matched_terms,
                        change_signals=change_signals,
                        confidence=_confidence(change_signals, matched_terms),
                        warnings=[
                            (
                                "Detected update candidate only. Verify the current official source before replacing "
                                "summaries."
                            )
                        ],
                    )
                )
        return DocumentationUpdateScanResult(candidates=candidates)


def _candidate_id(record: MessageRecord, tracked_title: str) -> str:
    seed = f"{record.source_id}:{tracked_title}:{record.source_hash or ''}"
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def _confidence(change_signals: list[str], matched_terms: list[str]) -> UpdateConfidence:
    if len(change_signals) >= 2 and len(matched_terms) >= 2:
        return UpdateConfidence.high
    if change_signals and matched_terms:
        return UpdateConfidence.medium
    return UpdateConfidence.low
