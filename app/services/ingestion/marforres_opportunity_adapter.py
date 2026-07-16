import hashlib
from datetime import date, datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.schemas.career_opportunities import (
    OpportunityParseResult,
    OpportunitySource,
    OpportunitySourceKey,
)
from app.schemas.opportunities import OpportunityRecord, OpportunityType

MAX_RESPONSE_BYTES = 5 * 1024 * 1024
ALLOWED_OPPORTUNITY_HOSTS = {
    "www.marforres.marines.mil",
    "marforres.marines.mil",
    "forms.osi.apps.mil",
}

OFFICIAL_OPPORTUNITY_SOURCES = {
    OpportunitySourceKey.reserve_billets: OpportunitySource(
        key=OpportunitySourceKey.reserve_billets,
        name="MARFORRES Reserve Billets",
        url="https://www.marforres.marines.mil/About/Reserve-Billets/",
        default_type=OpportunityType.smcr,
        description="Official MARFORRES gateway for SMCR and IMA billet opportunities.",
    ),
    OpportunitySourceKey.active_billets: OpportunitySource(
        key=OpportunitySourceKey.active_billets,
        name="MARFORRES Active Billets / Find",
        url=("https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-1-Administration/Active-Billets/Find/"),
        default_type=OpportunityType.ados,
        description="Official MARFORRES gateway for public active-duty and ADOS opportunities.",
    ),
}


class MarforresOpportunityAdapter:
    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch(self, source_key: OpportunitySourceKey) -> OpportunityParseResult:
        source = OFFICIAL_OPPORTUNITY_SOURCES[source_key]
        html = await self.fetch_url(source.url)
        return self.parse(html, source)

    async def fetch_url(self, url: str) -> str:
        canonical_urls = {source.url for source in OFFICIAL_OPPORTUNITY_SOURCES.values()}
        if url not in canonical_urls:
            raise ValueError("Opportunity source URL is not allowlisted.")
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            # follow_redirects is on, so the response may have landed on a
            # different host than the allowlisted one we requested. Re-check the
            # final URL before parsing so a redirect off an official source
            # cannot feed attacker-controlled HTML into the opportunity feed.
            if not _is_official_link(str(response.url)):
                raise ValueError("Official opportunity source redirected off an allowlisted host.")
            content_type = response.headers.get("content-type", "").casefold()
            if "html" not in content_type:
                raise ValueError("Official opportunity source did not return HTML.")
            if len(response.content) > MAX_RESPONSE_BYTES:
                raise ValueError("Official opportunity source response exceeded the size limit.")
            return response.text

    def parse(self, html: str, source: OpportunitySource) -> OpportunityParseResult:
        soup = BeautifulSoup(html, "html.parser")
        official_links = _official_links(soup, source.url)
        records: list[OpportunityRecord] = []
        source_order = 0
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            headers = [_normalize(cell.get_text(" ", strip=True)) for cell in rows[0].find_all(["th", "td"])]
            if not _looks_like_opportunity_table(headers):
                continue
            heading = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            section_label = heading.get_text(" ", strip=True) if isinstance(heading, Tag) else ""
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                values = {
                    headers[index]: cell.get_text(" ", strip=True)
                    for index, cell in enumerate(cells)
                    if index < len(headers)
                }
                title = _first(values, "title", "billet", "position", "billet_description", "bic_title")
                if not title:
                    continue
                source_order += 1
                direct_url = _first_official_row_link(row, source.url)
                opportunity_type = _opportunity_type(section_label, values, source.default_type)
                record = OpportunityRecord(
                    opportunity_id=_fingerprint(source.key, title, values),
                    title=title,
                    opportunity_type=opportunity_type,
                    unit=_first(values, "unit", "command", "section"),
                    location=_first(values, "location", "city_state", "address"),
                    rank=_first(values, "rank", "grade", "alpha_grade"),
                    rank_min=_first(values, "rank_min", "minimum_rank"),
                    rank_max=_first(values, "rank_max", "maximum_rank"),
                    mos=_first(values, "mos", "bmos", "pmos"),
                    duration=_first(values, "duration", "tour_length", "tour"),
                    published_at=_parse_date(_first(values, "published", "posted", "publication_date", "date")),
                    due_date=_parse_date(_first(values, "apply_by", "due_date", "deadline", "closing_date")),
                    source_url=source.url,
                    direct_url=direct_url,
                    source_name=source.name,
                    notes=_first(values, "notes", "remarks", "requirements"),
                    source_order=source_order,
                    tracked=False,
                )
                record.match_score = _actionability_score(record)
                records.append(record)
        warnings: list[str] = []
        if not records:
            warnings.append("Official source loaded, but no structured opportunity rows were available.")
        return OpportunityParseResult(
            source=source,
            records=_deduplicate(records),
            official_links=official_links,
            warnings=warnings,
        )


def _actionability_score(record: OpportunityRecord) -> int:
    """Rank how directly a listing can be acted on.

    The public feed has no per-user profile to match against, so "match score"
    scores actionability instead: a listing you can apply to directly, with a
    deadline and the rank/MOS/location a Marine needs to self-screen, ranks
    above a bare title. Sorting by this field surfaces the most complete,
    ready-to-pursue rows first. (A future per-profile match would layer on top.)
    """
    score = 0
    if record.direct_url:
        score += 3
    if record.due_date:
        score += 2
    if record.rank or record.rank_min or record.rank_max:
        score += 1
    if record.mos:
        score += 1
    if record.location:
        score += 1
    if record.published_at:
        score += 1
    return score


def _official_links(soup: BeautifulSoup, source_url: str) -> list[str]:
    links = {source_url}
    for anchor in soup.find_all("a", href=True):
        candidate = urljoin(source_url, str(anchor["href"]))
        if _is_official_link(candidate):
            links.add(candidate)
    return sorted(links)


def _first_official_row_link(row: Tag, source_url: str) -> str | None:
    for anchor in row.find_all("a", href=True):
        candidate = urljoin(source_url, str(anchor["href"]))
        if _is_official_link(candidate):
            return candidate
    return None


def _is_official_link(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").casefold() in ALLOWED_OPPORTUNITY_HOSTS


def _opportunity_type(
    section_label: str,
    values: dict[str, str],
    default: OpportunityType,
) -> OpportunityType:
    text = " ".join([section_label, values.get("component", ""), values.get("type", "")]).upper()
    if "IMA" in text:
        return OpportunityType.ima
    if "IA/JIA" in text or "IA JIA" in text:
        return OpportunityType.ia_jia
    if "ADOS" in text or "ACTIVE" in text:
        return OpportunityType.ados
    if "SMCR" in text:
        return OpportunityType.smcr
    return default


def _looks_like_opportunity_table(headers: list[str]) -> bool:
    return bool(
        {"title", "billet", "position", "billet_description", "bic_title"}.intersection(headers)
        and {"rank", "grade", "mos", "bmos", "location", "unit", "command"}.intersection(headers)
    )


def _normalize(value: str) -> str:
    return "_".join(value.casefold().replace("/", " ").replace("-", " ").split())


def _first(values: dict[str, str], *keys: str) -> str | None:
    return next((values[key] for key in keys if values.get(key)), None)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%d %b %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            continue
    return None


def _fingerprint(
    source_key: OpportunitySourceKey,
    title: str,
    values: dict[str, str],
) -> str:
    seed = "|".join(
        [
            source_key.value,
            title.casefold(),
            (_first(values, "unit", "command") or "").casefold(),
            (_first(values, "location", "city_state") or "").casefold(),
            (_first(values, "mos", "bmos", "pmos") or "").casefold(),
            (_first(values, "rank", "grade") or "").casefold(),
        ]
    )
    return hashlib.sha256(seed.encode()).hexdigest()[:24]


def _deduplicate(records: list[OpportunityRecord]) -> list[OpportunityRecord]:
    unique: dict[str, OpportunityRecord] = {}
    for record in records:
        unique.setdefault(record.opportunity_id, record)
    return list(unique.values())
