import hashlib


class LocalHashEmbeddingProvider:
    """Deterministic local stub for tests and offline development."""

    dimensions = 16

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest[: self.dimensions]]
