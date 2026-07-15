from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from app.schemas.billets import BilletSourceInfo, SmcrBillet

MARFORRES_BILLETS_URL = "https://www.marforres.marines.mil/About/Reserve-Billets/"
DAP_URL = (
    "https://www.manpower.marines.mil/Divisions/Manpower-Management/Enlisted-Assignments/"
    "Stay-Marine/Direct-Affiliation-Program/"
)
OFFICIAL_BILLET_SOURCE_URLS = {
    "marforres_billets": MARFORRES_BILLETS_URL,
    "manpower_dap": DAP_URL,
}


def official_billet_sources() -> list[BilletSourceInfo]:
    return [
        BilletSourceInfo(
            name="MARFORRES Reserve Billet Opportunities",
            url=MARFORRES_BILLETS_URL,
            description="Official gateway page for SMCR, IMA, and active duty billet listings.",
            warnings=[
                "Gateway pages may link to JavaScript applications that require browser interaction.",
                "Verify billet availability and eligibility through official Reserve channels.",
            ],
        ),
        BilletSourceInfo(
            name="Marine Corps Reserve Hub via Direct Affiliation Program",
            url=DAP_URL,
            description="Official DAP page linking to Reserve Hub search by location, MOS, and rank.",
            warnings=[
                "Reserve Hub results are live and may change regularly.",
                "Do not treat advisory recommendations as assignment approval.",
            ],
        ),
    ]


class SmcrBicScraper:
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch_html(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def parse(self, html: str, source_url: str) -> tuple[list[SmcrBillet], list[str]]:
        soup = BeautifulSoup(html, "html.parser")
        links = discover_reserve_hub_links(soup, source_url)
        billets = parse_billet_tables(soup, source_url)
        return billets, links


def discover_reserve_hub_links(soup: BeautifulSoup, source_url: str) -> list[str]:
    discovered: list[str] = []
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True).lower()
        href = str(anchor["href"])
        if "reserve hub" in label or "reservehub" in href.lower() or "billet" in label:
            discovered.append(urljoin(source_url, href))
    return sorted(set(discovered))


def parse_billet_tables(soup: BeautifulSoup, source_url: str) -> list[SmcrBillet]:
    billets: list[SmcrBillet] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [_normalize_header(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
        if not _looks_like_billet_table(headers):
            continue
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            values = {
                headers[index]: cell.get_text(" ", strip=True)
                for index, cell in enumerate(cells)
                if index < len(headers)
            }
            billet = _billet_from_row(values, source_url)
            if billet is not None:
                billets.append(billet)
    billets.extend(parse_billet_cards(soup, source_url))
    return billets


def parse_billet_cards(soup: BeautifulSoup, source_url: str) -> list[SmcrBillet]:
    billets: list[SmcrBillet] = []
    for element in soup.select("[data-bic]"):
        if not isinstance(element, Tag):
            continue
        billet = SmcrBillet(
            bic=str(element.get("data-bic") or ""),
            title=str(element.get("data-title") or element.get_text(" ", strip=True) or "Untitled billet"),
            unit=_optional_attr(element, "data-unit"),
            location=_optional_attr(element, "data-location"),
            rank=_optional_attr(element, "data-rank"),
            rank_min=_optional_attr(element, "data-rank-min"),
            rank_max=_optional_attr(element, "data-rank-max"),
            mos=_optional_attr(element, "data-mos"),
            source_url=source_url,
            notes=_optional_attr(element, "data-notes"),
        )
        billets.append(billet)
    return billets


def _billet_from_row(values: dict[str, str], source_url: str) -> SmcrBillet | None:
    title = _first(values, "title", "billet_description", "billet", "bic_title")
    bic = _first(values, "bic", "billet_identification_code")
    if not title and not bic:
        return None
    return SmcrBillet(
        bic=bic,
        title=title or "Untitled billet",
        unit=_first(values, "unit", "section", "command"),
        location=_first(values, "location", "address", "city_state"),
        rank=_first(values, "rank", "grade", "alpha_grade"),
        rank_min=_first(values, "rank_min", "minimum_rank"),
        rank_max=_first(values, "rank_max", "maximum_rank"),
        mos=_first(values, "mos", "bmos", "pmos"),
        source_url=source_url,
        notes=_first(values, "notes", "remarks", "requirements"),
    )


def _looks_like_billet_table(headers: list[str]) -> bool:
    return "bic" in headers or "bmos" in headers or "billet_description" in headers or "rank" in headers


def _normalize_header(header: str) -> str:
    return header.lower().replace("/", " ").replace("-", " ").replace(" ", "_")


def _first(values: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        value = values.get(key)
        if value:
            return value
    return None


def _optional_attr(element: Tag, name: str) -> str | None:
    value = element.get(name)
    return str(value) if value else None
