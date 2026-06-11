from pathlib import Path

from pypdf import PdfReader

MAX_PDF_PAGES = 25
MAX_PDF_TEXT_CHARS = 20_000


def extract_pdf_text(
    path: str | Path,
    max_pages: int = MAX_PDF_PAGES,
    max_chars: int = MAX_PDF_TEXT_CHARS,
) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages):
        if page_number >= max_pages:
            break
        pages.append(page.extract_text() or "")
        if sum(len(item) for item in pages) >= max_chars:
            break
    return "\n\n".join(pages).strip()[:max_chars]
