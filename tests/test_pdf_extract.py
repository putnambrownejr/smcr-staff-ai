from pathlib import Path

from pytest import MonkeyPatch

from app.services.ingestion import pdf_extract


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.pages = [_FakePage("page-1"), _FakePage("page-2"), _FakePage("page-3")]


def test_extract_pdf_text_limits_pages(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pdf_extract, "PdfReader", _FakePdfReader)

    result = pdf_extract.extract_pdf_text(tmp_path / "fake.pdf", max_pages=2)

    assert result == "page-1\n\npage-2"


def test_extract_pdf_text_limits_characters(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(pdf_extract, "PdfReader", _FakePdfReader)

    result = pdf_extract.extract_pdf_text(tmp_path / "fake.pdf", max_chars=10)

    assert result == "page-1\n\npa"
