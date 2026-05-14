import hashlib
from dataclasses import dataclass

from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.documents import DocumentRead
from app.services.rag.chunking import chunk_text
from app.services.rag.embeddings import LocalHashEmbeddingProvider
from app.services.rag.vector_store import LocalVectorStore, VectorRecord


@dataclass(frozen=True)
class RetrievalResult:
    text: str
    citation: StructuredCitation
    score_hint: float = 0.0


class LocalRagPipeline:
    def __init__(
        self,
        vector_store: LocalVectorStore | None = None,
        embedding_provider: LocalHashEmbeddingProvider | None = None,
    ) -> None:
        self.vector_store = vector_store or LocalVectorStore()
        self.embedding_provider = embedding_provider or LocalHashEmbeddingProvider()

    def ingest_text(self, document: DocumentRead, text: str) -> int:
        records: list[VectorRecord] = []
        for chunk in chunk_text(text):
            chunk_id = _chunk_id(document, chunk.chunk_index)
            records.append(
                VectorRecord(
                    id=chunk_id,
                    text=chunk.text,
                    vector=self.embedding_provider.embed(chunk.text),
                    metadata={
                        "source_id": document.source_id,
                        "title": document.title,
                        "url": document.url or "",
                        "issuing_org": document.issuing_org or "",
                        "classification_label": document.classification_label,
                        "cui_flag": str(document.cui_flag),
                        "source_hash": document.source_hash or "",
                        "version": document.version or "",
                        "effective_date": document.effective_date.isoformat() if document.effective_date else "",
                        "chunk_id": chunk_id,
                        "chunk_index": str(chunk.chunk_index),
                    },
                )
            )
        self.vector_store.upsert(records)
        return len(records)

    def retrieve(self, query: str, limit: int = 5) -> list[RetrievalResult]:
        results = []
        for record in self.vector_store.search(query, limit=limit):
            results.append(
                RetrievalResult(
                    text=record.text,
                    citation=StructuredCitation(
                        title=record.metadata.get("title", "Unknown source"),
                        url=record.metadata.get("url") or None,
                        publisher=record.metadata.get("issuing_org") or None,
                        source_hash=record.metadata.get("source_hash") or None,
                        document_version=record.metadata.get("version") or None,
                        effective_date=record.metadata.get("effective_date") or None,
                        chunk_id=record.metadata.get("chunk_id") or record.id,
                        confidence=Confidence.low,
                        notes=f"classification={record.metadata.get('classification_label', 'UNCLASSIFIED')}",
                    ),
                )
            )
        return results


def _chunk_id(document: DocumentRead, chunk_index: int) -> str:
    seed = f"{document.source_id}:{document.version or ''}:{document.source_hash or ''}:{chunk_index}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
