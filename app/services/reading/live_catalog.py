from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from app.schemas.reading import ReadingListBook, ReadingListCatalog, ReadingListSource
from app.services.reading.catalog import ReadingListCatalogService
from app.services.reading.catalog_store import ReadingListCatalogStore

OFFICIAL_CPRL_ALMAR_URL = (
    "https://www.marines.mil/News/Messages/Messages-Display/Article/4351724/"
    "update-to-the-commandants-professional-reading-list-for-fiscal-year-26/"
)
OFFICIAL_CPRL_GUIDE_URL = "https://grc-usmcu.libguides.com/cmc-reading-list"

_CATEGORY_MAP = {
    "commandant's choice": "commandants_choice",
    "heritage": "heritage",
    "innovation": "innovation",
    "leadership": "leadership",
    "strategy": "strategy",
    "foundational": "foundational",
}

_FALLBACK_SUMMARY = (
    "Current FY26 Commandant's Professional Reading List title pulled from the official ALMAR. "
    "Add local notes or curated study guidance for deeper use."
)


class ReadingListRemoteCatalogService:
    def __init__(
        self,
        seed_path: str | Path,
        source_url: str = OFFICIAL_CPRL_ALMAR_URL,
        guide_url: str = OFFICIAL_CPRL_GUIDE_URL,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.seed_path = Path(seed_path)
        self.source_url = source_url
        self.guide_url = guide_url
        self.timeout_seconds = timeout_seconds
        self._headers = {"User-Agent": "smcr-staff-ai/0.1 (+local advisory tool)"}

    def refresh(self, store: ReadingListCatalogStore) -> ReadingListCatalog:
        html_text = self._fetch_html()
        catalog = self.parse_official_current_catalog(html_text)
        store.save(catalog, self.source_url)
        return catalog

    def parse_official_current_catalog(self, html_text: str) -> ReadingListCatalog:
        seed_catalog = ReadingListCatalogService.from_yaml(self.seed_path).catalog
        seed_by_title = {_normalize_title(book.title): book for book in seed_catalog.books}
        books = _parse_current_books(html_text, seed_by_title, self.source_url, self.guide_url)
        sources = [
            ReadingListSource(
                name="FY26 Commandant's Professional Reading List ALMAR",
                url=self.source_url,
                source_type="official_almar",
                notes="Current official reading-list membership source for FY26.",
            ),
            ReadingListSource(
                name="Marine Corps University CPRL Guide",
                url=self.guide_url,
                source_type="official_library_guide",
                notes="Official MCU reading-program guide referenced by the ALMAR for current and archived material.",
            ),
        ]
        return ReadingListCatalog(
            notice=(
                "Current catalog built from the official FY26 ALMAR and cached locally. "
                "Use the ALMAR and MCU guide as the source of truth for current list membership."
            ),
            sources=sources,
            books=books,
        )

    def _fetch_html(self) -> str:
        with httpx.Client(timeout=self.timeout_seconds, headers=self._headers, follow_redirects=True) as client:
            response = client.get(self.source_url)
            response.raise_for_status()
        return response.text


def load_effective_reading_catalog(
    *,
    seed_path: str | Path,
    store: ReadingListCatalogStore,
) -> ReadingListCatalogService:
    snapshot = store.get()
    if snapshot is not None:
        return ReadingListCatalogService(snapshot.catalog)
    return ReadingListCatalogService.from_yaml(seed_path)


def _parse_current_books(
    html_text: str,
    seed_by_title: dict[str, ReadingListBook],
    source_url: str,
    guide_url: str,
) -> list[ReadingListBook]:
    soup = BeautifulSoup(html_text, "html.parser")
    lines = [
        " ".join(line.split())
        for line in soup.get_text("\n", strip=True).splitlines()
        if line and line.strip()
    ]
    current_category: str | None = None
    books: list[ReadingListBook] = []

    for line in lines:
        heading_match = re.match(r"^3\.[a-f]\.\s+(.+)$", line)
        if heading_match is not None:
            current_category, inline_book = _parse_category_heading(heading_match.group(1))
            if current_category is not None and inline_book:
                books.append(_build_book(inline_book, current_category, seed_by_title, source_url, guide_url))
            continue

        item_match = re.match(r"^3\.[a-f]\.\d+\.\s+(.+)$", line)
        if item_match is not None and current_category is not None:
            books.append(_build_book(item_match.group(1), current_category, seed_by_title, source_url, guide_url))

    return books


def _parse_category_heading(content: str) -> tuple[str | None, str | None]:
    normalized = content.replace("’", "'")
    lower = normalized.lower()
    for label, category in _CATEGORY_MAP.items():
        if lower.startswith(label):
            if ":" in normalized:
                _, remainder = normalized.split(":", 1)
                return category, remainder.strip() or None
            return category, None
    return None, None


def _build_book(
    raw_item: str,
    current_category: str,
    seed_by_title: dict[str, ReadingListBook],
    source_url: str,
    guide_url: str,
) -> ReadingListBook:
    title, author = _split_title_author(raw_item)
    seed_book = seed_by_title.get(_normalize_title(title))
    if seed_book is not None:
        categories = list(dict.fromkeys([*seed_book.categories, current_category, "current_list"]))
        list_years = list(dict.fromkeys([*seed_book.list_years, "2026"]))
        source_urls = list(dict.fromkeys([source_url, guide_url, *seed_book.source_urls]))
        return seed_book.model_copy(
            update={
                "categories": categories,
                "list_years": list_years,
                "source_urls": source_urls,
            }
        )

    return ReadingListBook(
        slug=_slugify(title),
        title=title,
        author=author,
        categories=[current_category, "current_list"],
        list_years=["2026"],
        open_source_available=False,
        public_domain=False,
        source_urls=[source_url, guide_url],
        summary=_FALLBACK_SUMMARY,
        key_themes=[],
        discussion_prompts=[],
        cautions=["Copyrighted work; store metadata, notes, and short study summaries only."],
    )


def _split_title_author(raw_item: str) -> tuple[str, str]:
    text = raw_item.strip().rstrip(".")
    for separator, suffix in ((" edited by ", " (editors)"), (" by ", "")):
        index = text.lower().rfind(separator)
        if index != -1:
            title = text[:index].strip().strip("\"“”")
            author = text[index + len(separator) :].strip()
            return title, f"{author}{suffix}"
    return text.strip("\"“”"), "Unknown"


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _slugify(title: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", title.lower()))
