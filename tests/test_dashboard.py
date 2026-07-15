from datetime import UTC, date, datetime, timedelta

_FUTURE_DRILL = date.today() + timedelta(days=21)
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.api.routes.dashboard as dashboard_routes  # noqa: E402
from app.api.routes.dashboard import (  # noqa: E402
    get_action_tracker,
    get_admin_service,
    get_alnav_store,
    get_battle_rhythm_store,
    get_career_service,
    get_chief_orchestrator,
    get_custom_watch_feed_store,
    get_document_organizer,
    get_dod_watch_store,
    get_navadmin_store,
    get_opportunity_tracker,
    get_section_memory_store,
    get_update_store,
)
from app.main import app  # noqa: E402
from app.schemas.actions import ActionItemRequest  # noqa: E402
from app.schemas.battle_rhythm import BattleRhythmBoardUpsertRequest, BattleRhythmEntryInput  # noqa: E402
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask  # noqa: E402
from app.schemas.custom_watch_feeds import CreateCustomWatchFeedRequest  # noqa: E402
from app.schemas.ingestion import MessageRecord  # noqa: E402
from app.schemas.opportunities import ManualOpportunityRequest  # noqa: E402
from app.schemas.section_memory import SectionMemoryEntry, SectionMemoryProfileUpsertRequest  # noqa: E402
from app.schemas.session import FitrepReminder, PmeStatus, UserSessionHandoff  # noqa: E402
from app.schemas.source_updates import DocumentationUpdateCandidate  # noqa: E402
from app.services.actions.tracker import ActionTracker  # noqa: E402
from app.services.admin.readiness import AdminReadinessService  # noqa: E402
from app.services.calendar.plan_store import DrillPrepPlanStore  # noqa: E402
from app.services.career.watch import CareerWatchService  # noqa: E402
from app.services.chief.orchestrator import ChiefAideOrchestrator  # noqa: E402
from app.services.connectors.travel_case_store import TravelCaseStore  # noqa: E402
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer  # noqa: E402
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore  # noqa: E402
from app.services.ingestion.document_update_store import DocumentUpdateStore  # noqa: E402
from app.services.ingestion.message_record_store import MessageRecordStore  # noqa: E402
from app.services.opportunities.tracker import OpportunityTracker  # noqa: E402
from app.services.reading.catalog import ReadingListCatalogService  # noqa: E402
from app.services.session.handoff_store import SessionHandoffStore  # noqa: E402
from app.services.staff.battle_rhythm_store import BattleRhythmStore  # noqa: E402
from app.services.staff.section_memory_store import SectionMemoryStore  # noqa: E402
from app.services.storage.local_context_store import LocalContextStore  # noqa: E402


def test_dashboard_route_serves_html_shell() -> None:
    client = TestClient(app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # The dashboard is a compiled, self-contained bundle.
    assert "__bundler/manifest" in response.text
    assert "Bench / Files" in response.text
    assert "A Few Good" in response.text
    # The route injects the file-open shim at serve time.
    assert "window.__SMCR_REPO_ROOT__" in response.text
    assert "/static/dashboard/reveal-shim.js" in response.text


def _decoded_dashboard_component_source() -> str:
    bundle_html = dashboard_routes._DASHBOARD_HTML.read_text(encoding="utf-8")
    template_open = '<script type="__bundler/template">'
    json_start = bundle_html.index(template_open) + len(template_open)
    json_end = bundle_html.index("</script>", json_start)
    decoded = json.loads(bundle_html[json_start:json_end].strip())
    assert isinstance(decoded, str)
    return decoded


def test_dashboard_bundle_is_wired_to_real_actions_api() -> None:
    """The compiled dashboard bundle is a static export from a design tool with
    all state (and demo data) hardcoded client-side -- see
    docs/superpowers/plans/2026-07-12-dashboard-bundle-remediation.md. This
    pins the real-backend wiring applied by scripts/patch_dashboard_bundle.py
    so a future bundle re-export can't silently drop it: fail loud here
    instead of failing silently at runtime in a browser.
    """
    component_source = _decoded_dashboard_component_source()

    assert "this._loadRealWorkspace();" in component_source
    assert "_resolveUserKey()" in component_source
    assert '"smcr_user_key"' in component_source
    assert "fetch(\"/dashboard/data/\"" in component_source
    assert "fetch(\"/actions/track\"" in component_source
    assert 'method: "PATCH"' in component_source
    assert 'fetch("/actions/" + encodeURIComponent(id), { method: "DELETE"' in component_source
    # Round-trips the free-text "due" stashed in notes back into the due field.
    assert "_mapRealAction(a)" in component_source
    assert "dueMatch" in component_source


def test_dashboard_bundle_renders_history_from_workspace_data() -> None:
    component_source = _decoded_dashboard_component_source()

    assert "data.today_in_history" in component_source
    assert "data.history_is_today" in component_source
    assert "historySpotlight" in component_source
    assert "{{ historyLabel }}" in component_source
    assert "{{ historyHeadline }}" in component_source
    assert "{{ historyDetails }}" in component_source
    assert "11 JUL 1798 — The U.S. Marine Corps was re-established" not in component_source


def test_dashboard_bundle_refreshes_real_feed_endpoints() -> None:
    component_source = _decoded_dashboard_component_source()

    assert "async _refreshFeeds()" in component_source
    assert 'url: "/maradmins/refresh"' in component_source
    assert 'url: "/message-watch/navadmins/refresh"' in component_source
    assert 'url: "/message-watch/alnavs/refresh"' in component_source
    assert 'url: "/message-watch/dod/refresh"' in component_source
    assert 'url: "/custom-watch-feeds/" + encodeURIComponent(feed.id) + "/refresh"' in component_source
    assert "failedLabels.join" in component_source
    assert "refreshFeeds: () => this._refreshFeeds()" in component_source
    assert 'refreshFeeds: () => this.setState({ feedUpdated: "just now" })' not in component_source


def test_dashboard_bundle_is_wired_to_real_feeds_links_and_handoff() -> None:
    """Same guard as the actions test above, for the feeds/links/profile wiring
    added in the same remediation pass (step 2, items 2-4)."""
    component_source = _decoded_dashboard_component_source()

    assert "this._loadRealFeeds();" in component_source
    assert "this._loadRealLinks();" in component_source
    assert "this._loadRealHandoff();" in component_source
    assert 'fetch("/custom-watch-feeds"' in component_source
    assert 'fetch("/custom-watch-feeds/" + encodeURIComponent(id), { method: "DELETE"' in component_source
    assert 'fetch("/resource-links/" + encodeURIComponent(this.userKey)' in component_source
    assert 'fetch("/handoffs/" + encodeURIComponent(this.userKey)' in component_source
    assert "_scheduleHandoffSave()" in component_source
    assert 'method: "PUT"' in component_source


def test_dashboard_reveal_shim_is_served() -> None:
    client = TestClient(app)

    response = client.get("/static/dashboard/reveal-shim.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert response.text.strip()


def test_dashboard_route_injects_pwa_metadata() -> None:
    # Lets the browser offer "Install SMCR Staff AI" as a standalone app
    # window (see scripts/launch_dashboard.pyw for the desktop-shortcut path).
    client = TestClient(app)

    response = client.get("/dashboard")

    assert '<link rel="manifest" href="/static/dashboard/manifest.webmanifest">' in response.text
    assert '<link rel="icon" type="image/png" sizes="32x32" href="/static/dashboard/icons/icon-32.png">' in response.text
    assert '<link rel="apple-touch-icon" href="/static/dashboard/icons/icon-192.png">' in response.text
    assert '<meta name="theme-color" content="#0d1014">' in response.text


def test_shutdown_route_schedules_termination(monkeypatch: pytest.MonkeyPatch) -> None:
    # The in-dash power button. Monkeypatch the scheduler -- actually running
    # it would terminate the test process.
    calls: list[bool] = []
    monkeypatch.setattr(dashboard_routes, "_schedule_shutdown", lambda: calls.append(True))
    client = TestClient(app)

    response = client.post("/dashboard/shutdown")

    assert response.status_code == 200
    assert response.json() == {"status": "shutting_down"}
    assert calls == [True]


def test_shutdown_requires_configured_local_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "shutdown-secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    calls: list[bool] = []
    monkeypatch.setattr(dashboard_routes, "_schedule_shutdown", lambda: calls.append(True))
    client = TestClient(app)

    without_key = client.post("/dashboard/shutdown")
    with_key = client.post("/dashboard/shutdown", headers={"X-Local-API-Key": "shutdown-secret"})

    assert without_key.status_code in (401, 403)
    assert with_key.status_code == 200
    assert calls == [True]
    get_settings.cache_clear()


def test_looks_like_server_wrapper_matches_reload_and_uv_parents() -> None:
    assert dashboard_routes._looks_like_server_wrapper(
        r'"C:\smcr-staff-ai\.venv\Scripts\python.exe" "C:\smcr-staff-ai\.venv\Scripts\uvicorn.exe" app.main:app --reload'
    )
    assert dashboard_routes._looks_like_server_wrapper("uv.exe run uvicorn app.main:app --host 127.0.0.1")
    assert not dashboard_routes._looks_like_server_wrapper(r"C:\Windows\explorer.exe")
    assert not dashboard_routes._looks_like_server_wrapper("")


def test_pwa_manifest_and_icons_are_served() -> None:
    client = TestClient(app)

    manifest = client.get("/static/dashboard/manifest.webmanifest")
    assert manifest.status_code == 200
    # Pinned in app/main.py -- Python's mimetypes doesn't know .webmanifest,
    # so without the pin this is application/octet-stream on some machines.
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    body = manifest.json()
    assert body["name"] == "SMCR Staff AI"
    assert body["start_url"] == "/dashboard"
    assert body["display"] == "standalone"
    icon_srcs = {icon["src"] for icon in body["icons"]}
    assert "/static/dashboard/icons/icon-192.png" in icon_srcs
    assert "/static/dashboard/icons/icon-512.png" in icon_srcs

    for src in sorted(icon_srcs):
        icon_response = client.get(src)
        assert icon_response.status_code == 200
        assert icon_response.headers["content-type"] == "image/png"
        assert icon_response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_reveal_is_open_when_no_local_api_key_is_configured() -> None:
    client = TestClient(app)

    response = client.get("/dashboard/files/reveal", params={"path": "README.md"})

    assert response.status_code == 200


def test_dashboard_shell_injects_configured_api_key_for_the_shim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "reveal-secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)

    response = client.get("/dashboard")

    assert "window.__SMCR_API_KEY__ = \"reveal-secret\"" in response.text
    get_settings.cache_clear()


def test_reveal_requires_configured_local_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_API_KEY", "reveal-secret")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)

    without_key = client.get("/dashboard/files/reveal", params={"path": "README.md"})
    wrong_key = client.get(
        "/dashboard/files/reveal",
        params={"path": "README.md"},
        headers={"X-Local-API-Key": "wrong"},
    )
    right_key = client.get(
        "/dashboard/files/reveal",
        params={"path": "README.md"},
        headers={"X-Local-API-Key": "reveal-secret"},
    )

    assert without_key.status_code == 401
    assert wrong_key.status_code == 401
    assert right_key.status_code == 200
    get_settings.cache_clear()


def test_reveal_rejects_paths_outside_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    response = client.get("/dashboard/files/reveal", params={"path": "../outside.txt"})

    assert response.status_code == 403
    assert opened == []


def test_reveal_resolves_user_docs_paths_through_the_digest_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # user_docs_dir has a computed static default baked in at Settings class
    # definition time (see app/core/config.py), so setting SMCR_STAFF_AI_HOME
    # here wouldn't retroactively change it -- monkeypatch the cached
    # settings instance's user_docs_dir attribute directly instead.
    from app.core.config import get_settings

    user_docs_dir = tmp_path / "User Docs"
    doc_dir = user_docs_dir / "Generations" / "abcdef0123456789abcdef01"
    doc_dir.mkdir(parents=True)
    (doc_dir / "4254ab7907b7.md").write_text("---\n---\n", encoding="utf-8")
    monkeypatch.setattr(get_settings(), "user_docs_dir", str(user_docs_dir))
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    # The dashboard shows drafts as "User Docs/<Category>/<id>.md" (no digest
    # level) and prefixes the repo root; both spellings must land on the real
    # file under the local state root.
    for raw in (
        "User Docs/Generations/4254ab7907b7.md",
        (dashboard_routes.REPO_ROOT / "User Docs/Generations/4254ab7907b7.md").as_posix(),
    ):
        opened.clear()
        response = client.get("/dashboard/files/reveal", params={"path": raw})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "opened"
        assert len(opened) == 1
        assert opened[0] == doc_dir / "4254ab7907b7.md"


def test_reveal_falls_back_to_the_user_docs_category_for_unknown_drafts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings

    user_docs_dir = tmp_path / "User Docs"
    (user_docs_dir / "Generations").mkdir(parents=True)
    monkeypatch.setattr(get_settings(), "user_docs_dir", str(user_docs_dir))
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    response = client.get(
        "/dashboard/files/reveal",
        params={"path": "User Docs/Generations/sitrep-pending-123.md"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "opened_fallback"
    assert len(opened) == 1
    assert opened[0] == user_docs_dir / "Generations"


def test_reveal_rejects_traversal_that_would_escape_local_state_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "user_docs_dir", str(tmp_path / "User Docs"))
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    response = client.get(
        "/dashboard/files/reveal",
        params={"path": "../../../../outside.txt"},
    )

    assert response.status_code == 403
    assert opened == []


def test_reveal_opens_existing_file_and_strips_fragment(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    response = client.get(
        "/dashboard/files/reveal",
        params={"path": "data/seed/system_templates.example.yaml#sys-opord"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "opened"
    assert body["resolved"].endswith("data/seed/system_templates.example.yaml")
    assert len(opened) == 1
    assert opened[0].name == "system_templates.example.yaml"


def test_reveal_falls_back_to_nearest_existing_ancestor(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[Path] = []
    monkeypatch.setattr(dashboard_routes, "_reveal_in_file_explorer", opened.append)
    client = TestClient(app)

    response = client.get(
        "/dashboard/files/reveal",
        params={"path": "personal/AT-orders-FY26.pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    # The exact path doesn't exist, so the endpoint must say so rather than
    # silently reporting success for a different path it opened instead.
    assert body["status"] == "opened_fallback"
    assert len(opened) == 1
    assert opened[0] == dashboard_routes.REPO_ROOT.resolve()




def test_demo_dashboard_data_route_returns_workspace_payload() -> None:
    client = TestClient(app)

    response = client.get("/demo/dashboard/data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "demo"
    assert payload["chief_brief"]["summary_lines"]
    assert payload["daily_ops_brief"]["executive_snapshot"]
    assert payload["analyst_brief"]["kpi_summary"]
    assert "history_library" in payload
    assert isinstance(payload["history_is_today"], bool)
    assert "reference_library" in payload
    assert any(item["official_links"] for item in payload["reference_library"])
    assert "tracked_opportunities" in payload


def test_personal_dashboard_data_route_returns_consolidated_payload(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")
    action_tracker = ActionTracker(tmp_path / "actions")
    update_store = DocumentUpdateStore(tmp_path / "updates")
    custom_feed_store = CustomWatchFeedStore(tmp_path / "custom_feeds")
    battle_rhythm_store = BattleRhythmStore(tmp_path / "battle_rhythm")
    section_memory_store = SectionMemoryStore(tmp_path / "section_memory")
    navadmin_store = MessageRecordStore(tmp_path / "navadmins")
    alnav_store = MessageRecordStore(tmp_path / "alnavs")
    dod_store = MessageRecordStore(tmp_path / "dod")
    reading_catalog = ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml"))

    context_store.save(
        filename="orders.txt",
        content=b"Training-only orders note.",
        content_type="text/plain",
        document_type="orders",
        consent_ack=True,
    )
    context_store.save(
        filename="MCWP 5-10 MCPP.txt",
        content=b"Marine Corps Planning Process reference",
        content_type="text/plain",
        document_type="reference_note",
        consent_ack=True,
    )
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-dash",
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 7, 1))],
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15), role="MRO")],
            admin_watch_items=["DTS voucher after drill"],
        )
    )
    plan_store.save(
        DrillPrepPlanResponse(
            id="plan-1",
            drill_date=_FUTURE_DRILL,
            tasks=[PrepTask(title="Pack gear", due_offset_days=3, due_date=date(2026, 6, 3), category="gear")],
        )
    )
    opportunity_tracker.track(
        [
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                unit="4th MLG",
                location="Remote",
                mos="0502",
                rank="Capt",
            )
        ]
    )
    action_tracker.track(
        [
            ActionItemRequest(
                user_key="capt-dash",
                title="Finalize drill POAM",
                owner="Capt Example",
                category="poam",
                priority="high",
                status="in_progress",
            )
        ]
    )
    update_store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="candidate-1",
                tracked_title="MCO 1610.7",
                trigger_type="maradmin",
                matched_terms=["fitrep"],
                change_signals=["update to"],
                detected_at=datetime(2026, 5, 1, tzinfo=UTC),
                source_published_at=datetime(2026, 4, 30, 14, 0, tzinfo=UTC),
            )
        ]
    )
    custom_feed_store.create(
        CreateCustomWatchFeedRequest(
            name="Unit updates",
            url="https://example.test/feed.xml",
            category="unit_news",
            trust_level="official",
            tags=["reserve"],
        )
    )
    navadmin_store.save_many(
        [
            MessageRecord(
                source_id="navadmin-001",
                title="NAVADMIN 001/26 Sample",
                canonical_url="https://example.test/navadmin-001",
                summary="Sample NAVADMIN summary.",
                source_family="NAVADMIN",
                published_at=datetime(2026, 4, 29, 13, 30, tzinfo=UTC),
            )
        ]
    )
    alnav_store.save_many(
        [
            MessageRecord(
                source_id="alnav-001",
                title="ALNAV 001/26 Sample",
                canonical_url="https://example.test/alnav-001",
                summary="Sample ALNAV summary.",
                source_family="ALNAV",
            )
        ]
    )
    dod_store.save_many(
        [
            MessageRecord(
                source_id="dod-001",
                title="DoD release sample",
                canonical_url="https://example.test/dod-001",
                summary="Sample DoD summary.",
                source_family="DoD",
            )
        ]
    )
    battle_rhythm_store.upsert(
        "capt-dash",
        BattleRhythmBoardUpsertRequest(
            board_title="June drill board",
            focus=["Protect training value", "Keep support honest"],
            assumption_log=[BattleRhythmEntryInput(text="Transport window remains workable.", section="S-4")],
            commander_decision_log=[BattleRhythmEntryInput(text="Approve one primary lane.", section="Command")],
            due_out_board=[BattleRhythmEntryInput(text="S-6: Confirm reporting method.", section="S-6")],
            next_touchpoint="Before the next drill sync, confirm assumptions and named due-outs.",
        ),
    )
    section_memory_store.upsert(
        "capt-dash",
        SectionMemoryProfileUpsertRequest(
            entries=[
                SectionMemoryEntry(
                    section="S-6",
                    title="Usual S-6 friction",
                    recurring_questions=["What access issue slows this unit first?"],
                    preferred_checks=["Force one primary reporting method before the final brief."],
                    notes=["This unit usually needs a comms simplification pass."],
                )
            ]
        ),
    )

    def override_orchestrator() -> ChiefAideOrchestrator:
        return ChiefAideOrchestrator(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            drill_plan_store=plan_store,
            reading_catalog=reading_catalog,
            document_update_store=update_store,
            opportunity_tracker=opportunity_tracker,
            travel_case_store=TravelCaseStore(tmp_path / "travel_cases"),
            battle_rhythm_store=battle_rhythm_store,
        )

    def override_admin() -> AdminReadinessService:
        return AdminReadinessService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            travel_case_store=TravelCaseStore(tmp_path / "admin_travel_cases"),
        )

    def override_career() -> CareerWatchService:
        return CareerWatchService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            opportunity_tracker=opportunity_tracker,
            reading_catalog=reading_catalog,
        )

    def override_organizer() -> PersonalDocumentOrganizer:
        return PersonalDocumentOrganizer(context_store)

    def override_tracker() -> OpportunityTracker:
        return opportunity_tracker

    def override_action_tracker() -> ActionTracker:
        return action_tracker

    def override_updates() -> DocumentUpdateStore:
        return update_store

    def override_custom_feed_store() -> CustomWatchFeedStore:
        return custom_feed_store

    def override_battle_rhythm_store() -> BattleRhythmStore:
        return battle_rhythm_store

    def override_navadmin_store() -> MessageRecordStore:
        return navadmin_store

    def override_alnav_store() -> MessageRecordStore:
        return alnav_store

    def override_dod_store() -> MessageRecordStore:
        return dod_store

    def override_section_memory_store() -> SectionMemoryStore:
        return section_memory_store

    app.dependency_overrides[get_chief_orchestrator] = override_orchestrator
    app.dependency_overrides[get_admin_service] = override_admin
    app.dependency_overrides[get_career_service] = override_career
    app.dependency_overrides[get_document_organizer] = override_organizer
    app.dependency_overrides[get_action_tracker] = override_action_tracker
    app.dependency_overrides[get_opportunity_tracker] = override_tracker
    app.dependency_overrides[get_update_store] = override_updates
    app.dependency_overrides[get_custom_watch_feed_store] = override_custom_feed_store
    app.dependency_overrides[get_battle_rhythm_store] = override_battle_rhythm_store
    app.dependency_overrides[get_navadmin_store] = override_navadmin_store
    app.dependency_overrides[get_alnav_store] = override_alnav_store
    app.dependency_overrides[get_dod_watch_store] = override_dod_store
    app.dependency_overrides[get_section_memory_store] = override_section_memory_store

    client = TestClient(app)
    try:
        response = client.get("/dashboard/data/capt-dash")
        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] == "personal"
        assert payload["chief_brief"]["user_key"] == "capt-dash"
        assert payload["chief_brief"]["next_drill_readiness"]["anchor_drill_date"] == _FUTURE_DRILL.isoformat()
        assert payload["chief_brief"]["next_drill_readiness"]["decisive_action"]
        assert payload["chief_brief"]["next_drill_readiness"]["this_week_focus"]
        assert payload["chief_brief"]["next_drill_readiness"]["ready_if"]
        assert payload["chief_brief"]["walk_in_brief_pack"]["current_state"]
        assert payload["chief_brief"]["walk_in_brief_pack"]["before_you_walk_in"]
        assert payload["chief_brief"]["next_drill_readiness"]["must_do_before_drill"]
        assert payload["daily_ops_brief"]["must_do"]
        assert payload["analyst_brief"]["data_quality_notes"]
        assert payload["tracked_actions"][0]["title"] == "Finalize drill POAM"
        assert payload["document_summary"]["total_documents"] == 2
        assert payload["tracked_opportunities"][0]["title"] == "ADOS Planner"
        assert payload["documentation_updates"][0]["tracked_title"] == "MCO 1610.7"
        assert payload["documentation_updates"][0]["source_published_at"] == "2026-04-30T14:00:00Z"
        assert payload["custom_watch_feeds"][0]["name"] == "Unit updates"
        assert payload["battle_rhythm"]["board_title"] == "June drill board"
        assert payload["section_memory_profile"]["entries"][0]["section"] == "S-6"
        assert payload["chief_brief"]["battle_rhythm_summary"]
        assert "history_library" in payload
        assert payload["reference_library"]
        assert any(item["official_links"] for item in payload["reference_library"])
        suggested = next(item for item in payload["document_details"] if item["filename"] == "MCWP_5-10_MCPP.txt")
        assert suggested["suggested_document_type"] == "doctrine"
        assert suggested["suggestion_reason"]
        assert payload["navadmin_ticker"][0]["status"] == "NAVADMIN"
        assert payload["navadmin_ticker"][0]["published_at"] == "2026-04-29T13:30:00+00:00"
        assert payload["alnav_ticker"][0]["status"] == "ALNAV"
        assert payload["dod_ticker"][0]["status"] == "DoD"
        system_template = next(item for item in payload["template_library"] if item["template_source"] == "system")
        assert system_template["source_path"].startswith("data/templates/system/")
        assert "#sys-" not in system_template["source_path"]
        assert Path(system_template["source_path"]).is_file()
    finally:
        app.dependency_overrides.clear()
