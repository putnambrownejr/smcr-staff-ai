"""Tests for module pack discovery, ingestion, and route."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.staff.module_discovery import ModuleDiscovery

# ---------------------------------------------------------------------------
# Discovery unit tests
# ---------------------------------------------------------------------------

@pytest.fixture
def modules_dir(tmp_path: Path) -> Path:
    pack = tmp_path / "alpha-pack"
    pack.mkdir()
    (pack / "manifest.json").write_text(
        json.dumps({"title": "Alpha Pack", "description": "Test pack.", "author": "HQ", "version": "1.0"}),
        encoding="utf-8",
    )
    (pack / "sop-logpac.md").write_text("# LOGPAC SOP\nContent here.", encoding="utf-8")
    (pack / "notes.txt").write_text("Plain text notes.", encoding="utf-8")
    (pack / "ignored.exe").write_text("binary", encoding="utf-8")

    empty = tmp_path / "empty-pack"
    empty.mkdir()
    return tmp_path


def test_discovery_lists_packs(modules_dir: Path) -> None:
    d = ModuleDiscovery(modules_dir)
    packs = d.list_packs()
    assert len(packs) == 2
    names = [p.pack_name for p in packs]
    assert "alpha-pack" in names
    assert "empty-pack" in names


def test_discovery_reads_manifest(modules_dir: Path) -> None:
    d = ModuleDiscovery(modules_dir)
    packs = {p.pack_name: p for p in d.list_packs()}
    alpha = packs["alpha-pack"]
    assert alpha.manifest.title == "Alpha Pack"
    assert alpha.manifest.author == "HQ"
    assert alpha.supported_file_count == 2


def test_discovery_unsupported_files_excluded(modules_dir: Path) -> None:
    d = ModuleDiscovery(modules_dir)
    detail = d.get_pack("alpha-pack")
    filenames = [f.filename for f in detail.files]
    assert "ignored.exe" not in filenames
    assert "manifest.json" not in filenames


def test_discovery_missing_dir_returns_empty() -> None:
    d = ModuleDiscovery("/nonexistent/path")
    assert d.list_packs() == []
    assert d.get_pack("any") is None


def test_discovery_pack_file_path_traversal_blocked(modules_dir: Path) -> None:
    d = ModuleDiscovery(modules_dir)
    assert d.pack_file_path("alpha-pack", "../other-pack/secret.md") is None


def test_discovery_no_manifest_uses_folder_name(modules_dir: Path) -> None:
    d = ModuleDiscovery(modules_dir)
    detail = d.get_pack("empty-pack")
    assert detail is not None
    assert "Empty" in detail.manifest.title or "empty" in detail.manifest.title.lower()


# ---------------------------------------------------------------------------
# Route integration tests
# ---------------------------------------------------------------------------

@pytest.fixture
def module_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    pack = tmp_path / "test-pack"
    pack.mkdir()
    (pack / "manifest.json").write_text(
        json.dumps({"title": "Test Pack", "description": "Integration test pack."}),
        encoding="utf-8",
    )
    (pack / "doc.md").write_text("# Doc\nHello.", encoding="utf-8")

    monkeypatch.setenv("MODULE_PACKS_DIR", str(tmp_path))
    monkeypatch.setenv("LOCAL_CONTEXT_STORAGE_DIR", str(tmp_path / "context"))
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_list_packs(module_client: TestClient) -> None:
    resp = module_client.get("/modules")
    assert resp.status_code == 200
    packs = resp.json()
    assert len(packs) == 1
    assert packs[0]["pack_name"] == "test-pack"
    assert packs[0]["manifest"]["title"] == "Test Pack"


def test_get_pack_detail(module_client: TestClient) -> None:
    resp = module_client.get("/modules/test-pack")
    assert resp.status_code == 200
    data = resp.json()
    assert data["file_count"] == 1
    assert data["files"][0]["filename"] == "doc.md"


def test_get_pack_not_found(module_client: TestClient) -> None:
    resp = module_client.get("/modules/does-not-exist")
    assert resp.status_code == 404


def test_ingest_pack(module_client: TestClient) -> None:
    resp = module_client.post("/modules/test-pack/ingest")
    assert resp.status_code == 200
    data = resp.json()
    assert "doc.md" in data["ingested"]
    assert data["skipped"] == []
    assert data["replaced"] == 0
    assert "1 file" in data["message"]


def test_ingest_pack_idempotent(module_client: TestClient) -> None:
    module_client.post("/modules/test-pack/ingest")
    resp2 = module_client.post("/modules/test-pack/ingest")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["replaced"] == 1
    assert "doc.md" in data["ingested"]


def test_ingest_pack_not_found(module_client: TestClient) -> None:
    resp = module_client.post("/modules/ghost-pack/ingest")
    assert resp.status_code == 404
