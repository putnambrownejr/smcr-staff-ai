from app.services.rag.vector_store import LocalVectorStore, VectorRecord


class Retriever:
    def __init__(self, vector_store: LocalVectorStore | None = None) -> None:
        self.vector_store = vector_store or LocalVectorStore()

    def retrieve(self, query: str, limit: int = 5) -> list[VectorRecord]:
        return self.vector_store.search(query=query, limit=limit)
