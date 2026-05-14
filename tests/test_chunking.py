from app.services.rag.chunking import chunk_text


def test_chunking_returns_stable_chunks() -> None:
    text = "Alpha bravo charlie. " * 120
    chunks = chunk_text(text, max_chars=120, overlap=20)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text.startswith("Alpha")
    assert chunks == chunk_text(text, max_chars=120, overlap=20)
