from dataclasses import dataclass


@dataclass(frozen=True)
class VectorRecord:
    id: str
    text: str
    vector: list[float]
    metadata: dict[str, str]


class LocalVectorStore:
    """In-memory vector store stub with lexical scoring for early development."""

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        for record in records:
            self._records[record.id] = record

    def search(self, query: str, limit: int = 5) -> list[VectorRecord]:
        terms = {term.lower() for term in query.split()}
        scored = sorted(
            self._records.values(),
            key=lambda record: len(terms.intersection(record.text.lower().split())),
            reverse=True,
        )
        return scored[:limit]
