import hashlib
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup

from app.schemas.ingestion import PublicationRecord


def load_doctrine_manifest(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return dict(payload)


def parse_mcpel_article_html(html: str, canonical_url: str) -> PublicationRecord:
    soup = BeautifulSoup(html, "html.parser")
    title = " ".join((soup.title.string if soup.title and soup.title.string else "MCPEL publication").split())
    heading = soup.find(["h1", "h2"])
    if heading is not None:
        title = " ".join(heading.get_text(" ", strip=True).split()) or title
    publication_number = _publication_number(title)
    source_seed = publication_number or canonical_url
    source_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
    return PublicationRecord(
        source_id=f"mcpel-{hashlib.sha256(source_seed.encode('utf-8')).hexdigest()[:16]}",
        title=title,
        canonical_url=canonical_url,
        publication_number=publication_number,
        source_hash=source_hash,
        parser_warnings=[] if publication_number else ["Could not parse publication number from title."],
    )


def _publication_number(title: str) -> str | None:
    tokens = ("MCDP", "MCWP", "MCTP", "MCRP", "MCO", "NAVMC")
    for token in tokens:
        if token in title.upper():
            start = title.upper().find(token)
            return title[start:].split(" ", maxsplit=2)[0] + (
                f" {title[start:].split(' ', maxsplit=2)[1]}" if len(title[start:].split(" ", maxsplit=2)) > 1 else ""
            )
    return None
