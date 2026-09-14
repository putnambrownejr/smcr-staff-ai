import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.public_library.catalog import PublicCatalog
from app.public_library.models import DRAFT_NOTICE, SourceLink
from app.public_library.settings import PublicSettings


def test_snapshot_search_pagination_and_currency() -> None:
    catalog = PublicCatalog.load()
    first = catalog.search(limit=3)
    second = catalog.search(limit=3, offset=3)
    assert len(first.items) == len(second.items) == 3
    assert not {item.id for item in first.items} & {item.id for item in second.items}
    assert first.next_offset == 3
    assert first.total == 22
    assert first.notice == DRAFT_NOTICE
    templates = catalog.search("AAR", category="template")
    assert templates.items[0].id == "sys-aar"
    item = catalog.get("sys-aar")
    assert "## Draft scaffold" in item.content
    assert "118 Marines" not in item.content  # notional worked examples are not published
    assert item.last_verified_at is None
    assert item.verification_status == "not_live_verified"
    assert item.sources


@pytest.mark.parametrize("query,limit,offset", [("a" * 201, 5, 0), ("", 0, 0), ("", 31, 0), ("", 2, -1)])
def test_search_bounds(query: str, limit: int, offset: int) -> None:
    with pytest.raises(ValueError):
        PublicCatalog.load().search(query, limit=limit, offset=offset)


@pytest.mark.parametrize("item_id", ["../../.env", "C:/secrets", "file:///etc/passwd", "new-private-pack", ""])
def test_only_catalog_ids_are_readable(item_id: str) -> None:
    with pytest.raises(ValueError, match="Unknown library ID"):
        PublicCatalog.load().get(item_id)


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///etc/passwd", "http://example.org", "https://user:pass@example.org"])
def test_unsafe_source_links_are_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        SourceLink(title="Bad URL", url=url)


@pytest.mark.parametrize("url", ["http://example.org", "https://example.org/path", "https://user:pass@example.org", "https://example.org?query=yes"])
def test_public_origin_must_be_explicit_and_safe(url: str) -> None:
    with pytest.raises(ValidationError):
        PublicSettings(base_url=url)


def test_local_settings_and_new_files_cannot_leak_into_public_catalog(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    root = Path(__file__).resolve().parents[2]
    (tmp_path / ".env").write_text("LOCAL_API_KEY=do-not-load\n", encoding="utf-8")
    (tmp_path / "private.md").write_text("private-canary-string", encoding="utf-8")
    code = """
import json, sys
from pathlib import Path
from app.public_library.app import app
from app.public_library.catalog import PublicCatalog
assert 'app.main' not in sys.modules
assert 'app.core.config' not in sys.modules
assert not any(name.startswith('app.services.') for name in sys.modules)
assert not Path('state').exists()
assert not Path('projects').exists()
assert PublicCatalog.load().search('private-canary-string').total == 0
print(json.dumps({'items': PublicCatalog.load().search().total}))
"""
    environment = {
        **os.environ, "PYTHONPATH": str(root), "SMCR_STAFF_AI_HOME": str(tmp_path / "state"),
        "PROJECTS_DIR": str(tmp_path / "projects"),
    }
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=environment, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["items"] == 22


def test_publication_snapshot_is_reproducible() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, str(root / "scripts/build_public_catalog.py"), "--check"],
        cwd=root, text=True, capture_output=True, check=True,
    )
    assert "matches its allowlisted sources" in result.stdout
