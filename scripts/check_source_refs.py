"""Link-check every SourceRef URL in app/services/agents/source_refs.py.

Usage:
    uv run python scripts/check_source_refs.py            # check all, print a report
    uv run python scripts/check_source_refs.py --json out.json

Notes
-----
* marines.mil, usmcu.edu, and several other DoD hosts sit behind a WAF that
  answers every scripted request with HTTP 403. Those are reported as
  "blocked" (not broken) and must be verified by hand or via a search engine;
  the MCPEL article id in the URL is the thing to compare.
* Duplicate article ids for *different* titles are reported as errors because
  at least one of them is wrong.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.agents import source_refs as refs  # noqa: E402

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
_ARTICLE_ID = re.compile(r"/Article/(\d+)/", re.IGNORECASE)


def _all_refs() -> list[tuple[str, refs.SourceRef]]:
    seen: dict[str, refs.SourceRef] = {}
    groups: list[tuple[str, refs.SourceRef]] = []
    for name in dir(refs):
        if not name.endswith("_REFERENCES"):
            continue
        value = getattr(refs, name)
        if not isinstance(value, tuple):
            continue
        for ref in value:
            if isinstance(ref, refs.SourceRef) and ref.url not in seen:
                seen[ref.url] = ref
                groups.append((name, ref))
    return groups


def _check(url: str, client: httpx.Client) -> tuple[str, int | None]:
    try:
        response = client.get(url)
    except httpx.HTTPError as exc:
        return f"error: {type(exc).__name__}", None
    if response.status_code == 403:
        return "blocked (WAF) — verify by hand", 403
    if response.status_code >= 400:
        return "broken", response.status_code
    return "ok", response.status_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    entries = _all_refs()
    by_article: dict[str, set[str]] = defaultdict(set)
    rows: list[dict[str, object]] = []
    with httpx.Client(headers={"User-Agent": _UA}, follow_redirects=True, timeout=args.timeout) as client:
        for group, ref in entries:
            status, code = _check(ref.url, client)
            match = _ARTICLE_ID.search(ref.url)
            if match:
                by_article[match.group(1)].add(ref.title.split(" (")[0])
            rows.append({"group": group, "title": ref.title, "url": ref.url, "status": status, "code": code})
            print(f"{status:32} {code or '-':>4}  {ref.title[:70]}")

    duplicates = {aid: titles for aid, titles in by_article.items() if len(titles) > 1}
    print()
    print(f"{len(rows)} unique URLs checked.")
    for label in ("ok", "broken", "blocked (WAF) — verify by hand"):
        print(f"  {label}: {sum(1 for row in rows if row['status'] == label)}")
    errors = sum(1 for row in rows if str(row["status"]).startswith("error"))
    print(f"  network errors: {errors}")
    if duplicates:
        print("\nMCPEL article ids shared by different titles (at least one is wrong):")
        for aid, titles in sorted(duplicates.items()):
            print(f"  {aid}: {' | '.join(sorted(titles))}")
    if args.json:
        args.json.write_text(json.dumps({"rows": rows, "duplicates": duplicates}, indent=2), encoding="utf-8")
    broken = sum(1 for row in rows if row["status"] == "broken")
    return 1 if broken or duplicates else 0


if __name__ == "__main__":
    raise SystemExit(main())
