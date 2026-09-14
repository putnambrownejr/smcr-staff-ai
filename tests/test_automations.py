"""Tests for user-defined automations: store, block rendering, routes, and run packets."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.schemas.automations import AutomationUpsertRequest
from app.services.chief.automation_store import AUTOMATION_TEMPLATES, AutomationStore, build_automation_block


@pytest.fixture()
def automation_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    settings = get_settings()
    monkeypatch.setattr(settings, "automations_storage_dir", str(tmp_path / "automations"))
    monkeypatch.setattr(settings, "chief_setup_storage_dir", str(tmp_path / "chief_setup"))
    monkeypatch.setattr(settings, "user_docs_dir", str(tmp_path / "user_docs"))
    return tmp_path


def test_store_creates_updates_and_deletes(automation_dirs: Path) -> None:
    store = AutomationStore(automation_dirs / "automations")
    created = store.create(
        "user-a",
        AutomationUpsertRequest(name="  MARADMIN watch ", agents=["chief-of-staff", "chief-of-staff"], steps=["a", " ", "a"]),
    )
    assert created.name == "MARADMIN watch"
    assert created.agents == ["chief-of-staff"]
    assert created.steps == ["a"]
    updated = store.update("user-a", created.id, AutomationUpsertRequest(name="MARADMIN watch v2"))
    assert updated is not None and updated.name == "MARADMIN watch v2"
    assert [item.id for item in store.list_all("user-a")] == [created.id]
    assert store.delete("user-a", created.id) is True
    assert store.list_all("user-a") == []


def test_block_carries_steps_seats_inputs_and_safety_footer() -> None:
    store_request = AutomationUpsertRequest(
        name="Post-drill admin sweep",
        purpose="Close the loop.",
        trigger="Within 5 days after drill",
        cadence="Monthly",
        steps=["Check DTS vouchers", "List open corrections"],
        inputs_needed=["Drill dates"],
        output_format="Due-out tracker",
    )
    automation = AutomationStore.__new__(AutomationStore)  # not needed for rendering; build directly
    from app.schemas.automations import Automation

    record = Automation(id="abc", user_key="u", **store_request.model_dump())
    block = build_automation_block(record, chief_setup=None, seat_lines=["S-1 / G-1 / Administration (staff-s1) — Admin"])
    assert block.startswith('You are running my "Post-drill admin sweep" automation')
    assert "1. Check DTS vouchers" in block and "2. List open corrections" in block
    assert "S-1 / G-1 / Administration (staff-s1)" in block
    assert "- Drill dates" in block
    assert "Format: Due-out tracker" in block
    assert "DRAFT — Verify all references" in block
    del automation


def test_routes_round_trip_with_templates_and_run_packet(automation_dirs: Path) -> None:
    client = TestClient(app)
    templates = client.get("/automations/templates").json()
    assert {item["key"] for item in templates} >= {"post_drill_admin_sweep", "range_day_package"}
    assert all(item["agents"] for item in templates)

    template = next(item for item in templates if item["key"] == "range_day_package")
    created = client.post(
        "/automations/user-r",
        json={
            "name": template["name"],
            "purpose": template["purpose"],
            "trigger": template["trigger"],
            "cadence": template["cadence"],
            "agents": template["agents"],
            "steps": template["steps"],
            "inputs_needed": template["inputs_needed"],
            "output_format": template["output_format"],
            "template_key": template["key"],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    automation_id = body["automation"]["id"]
    assert "OpsO / S-3 / G-3" in body["agent_names"]
    assert "RFMSS" in body["block"]

    listed = client.get("/automations/user-r").json()["automations"]
    assert [item["automation"]["id"] for item in listed] == [automation_id]

    packet = client.post(
        f"/automations/user-r/{automation_id}/packet",
        json={"input": "Range day 18 OCT at Camp Lejeune, 60 Marines, M4 tables 1-2, 9,000 rounds 5.56 forecast.", "save": True},
    )
    assert packet.status_code == 200, packet.text
    data = packet.json()
    assert data["participants"] == template["agents"]
    assert "## Standing instruction (my automation)" in data["packet_markdown"]
    assert "Run the standing instruction above" in data["packet_markdown"]
    assert "No AI has run and nothing below is analysis" in data["packet_markdown"]
    assert data["saved_doc_id"]
    drafts = client.get("/user-docs/generations/user-r").json()
    assert any(entry["id"] == data["saved_doc_id"] and entry["title"].startswith("Automation run") for entry in drafts)

    unknown_agent = client.post("/automations/user-r", json={"name": "x", "agents": ["not-an-agent"]})
    assert unknown_agent.status_code == 422
    assert client.delete(f"/automations/user-r/{automation_id}").status_code == 204
    assert client.get("/automations/user-r").json()["automations"] == []
    assert client.delete(f"/automations/user-r/{automation_id}").status_code == 404


def test_templates_only_reference_registered_agents() -> None:
    from app.services.agents.registry import agent_registry

    for template in AUTOMATION_TEMPLATES:
        for agent_id in template.agents:
            assert agent_registry.get(agent_id) is not None, f"{template.key}: {agent_id}"
