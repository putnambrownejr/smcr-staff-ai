from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.family_readiness import (
    get_family_readiness_store,
    get_family_readiness_user_docs_store,
)
from app.main import app
from app.schemas.family_readiness import FamilyReadinessEventCreateRequest, ReadinessDurationBand
from app.services.agents.base import AgentContext
from app.services.agents.registry import agent_registry, category_for_agent
from app.services.family_readiness.builder import build_event, render_spouse_summary
from app.services.family_readiness.store import FamilyReadinessStore
from app.services.user_docs.store import UserDocsStore


def test_extended_at_builds_short_readiness_event() -> None:
    event = build_event(
        FamilyReadinessEventCreateRequest(
            user_key="capt-family",
            title="Extended AT 2027",
            approximate_start=date(2027, 7, 1),
            approximate_end=date(2027, 7, 28),
        )
    )

    assert event.duration_band is ReadinessDurationBand.short
    assert {item.category.value for item in event.items} >= {"legal", "deers", "contacts", "opsec"}
    assert any(item.source_url and "tricare.mil/DEERS" in item.source_url for item in event.items)
    assert any(milestone.label.startswith("T-") for milestone in event.milestones)


def test_summary_excludes_private_and_nonshareable_content() -> None:
    event = build_event(FamilyReadinessEventCreateRequest(user_key="capt-family", title="Overseas orders 2028"))
    event.private_notes = "Private note"
    event.items[0].shareable = False
    hidden_task = event.items[0].task

    summary = render_spouse_summary(event)

    assert "Private note" not in summary
    assert hidden_task not in summary
    assert "DRAFT — Verify all references" in summary


def test_store_persists_user_scoped_progress(tmp_path: Path) -> None:
    store = FamilyReadinessStore(tmp_path / "family-readiness")
    event = store.create(FamilyReadinessEventCreateRequest(user_key="capt-family", title="Extended AT"))

    updated = store.update_item(
        "capt-family",
        event.event_id,
        event.items[0].item_id,
        {"status": "complete", "notes": "Reviewed"},
    )

    assert updated.items[0].status.value == "complete"
    assert store.get("capt-family", event.event_id) == updated
    assert store.list("different-user") == []


def test_routes_create_update_export_and_summarize(tmp_path: Path) -> None:
    store = FamilyReadinessStore(tmp_path / "family-readiness")
    user_docs = UserDocsStore(tmp_path / "user-docs", tmp_path / "projects")
    app.dependency_overrides[get_family_readiness_store] = lambda: store
    app.dependency_overrides[get_family_readiness_user_docs_store] = lambda: user_docs
    client = TestClient(app)
    try:
        created = client.post(
            "/family-readiness/capt-family",
            json={
                "user_key": "capt-family",
                "title": "Extended AT 2027",
                "approximate_start": "2027-07-01",
                "approximate_end": "2027-07-28",
            },
        )
        assert created.status_code == 201
        event_id = created.json()["event_id"]
        item_id = created.json()["items"][0]["item_id"]

        updated = client.patch(
            f"/family-readiness/capt-family/{event_id}/items/{item_id}",
            json={"status": "complete"},
        )
        assert updated.status_code == 200
        assert updated.json()["items"][0]["status"] == "complete"

        ics = client.get(f"/family-readiness/capt-family/{event_id}/ics")
        assert ics.status_code == 200
        assert ics.text.startswith("BEGIN:VCALENDAR")
        assert "LOCATION:" not in ics.text

        summary = client.post(
            f"/family-readiness/capt-family/{event_id}/summary",
            json={"user_key": "capt-family"},
        )
        assert summary.status_code == 201
        assert summary.json()["fields"]["templateType"] == "family_readiness_summary"
    finally:
        app.dependency_overrides.clear()


def test_family_deployment_readiness_agent_is_registered_and_safe() -> None:
    agent = agent_registry.get("family-deployment-readiness-advisor")

    assert agent is not None
    assert category_for_agent(agent.metadata.id) == "Reserve Admin & Readiness"
    response = agent.run("Help me prepare for a 30-day AT", AgentContext())
    assert "power of attorney" in response.answer.lower()
    assert "DRAFT — Verify all references" in response.answer
    assert any("mission" in value.lower() for value in agent.metadata.disallowed_inputs)
