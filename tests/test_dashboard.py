from datetime import UTC, date, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.dashboard import (
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
from app.main import app
from app.schemas.actions import ActionItemRequest
from app.schemas.battle_rhythm import BattleRhythmBoardUpsertRequest, BattleRhythmEntryInput
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.custom_watch_feeds import CreateCustomWatchFeedRequest
from app.schemas.ingestion import MessageRecord
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.section_memory import SectionMemoryEntry, SectionMemoryProfileUpsertRequest
from app.schemas.session import FitrepReminder, PmeStatus, UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate
from app.services.actions.tracker import ActionTracker
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.career.watch import CareerWatchService
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.staff.section_memory_store import SectionMemoryStore
from app.services.storage.local_context_store import LocalContextStore


def test_dashboard_route_serves_html_shell() -> None:
    client = TestClient(app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SMCR Staff AI" in response.text
    assert "Next Drill Readiness" in response.text
    assert "Thin Staff Assist" in response.text
    assert "Walk-In Brief Pack" in response.text
    assert "Decisive action now" in response.text
    assert "Staff update cycle" in response.text
    assert "Planning Cell" in response.text
    assert "Brief Clinic" in response.text
    assert "Uniform Photo Review" in response.text
    assert "Time watch" in response.text
    assert "Time zones" in response.text
    assert "Battle Rhythm Board" in response.text
    assert "Continuity watch" in response.text
    assert "Section Bench Notebook" in response.text
    assert "MOS bench" in response.text
    assert "MOS advisor" in response.text
    assert "Marine Corps History Facts" in response.text
    assert "Doctrine / Reference Library" in response.text
    assert "Use suggestion" in response.text
    assert "Show facts" in response.text
    assert "Use today" in response.text
    assert 'id="history-library-month"' in response.text
    assert 'id="history-library-day"' in response.text
    assert 'id="reference-select"' in response.text
    assert "Open reference library" in response.text
    assert "Save section memory" in response.text
    assert "Save battle rhythm board" in response.text
    assert "Open reading tracker" in response.text
    assert 'id="reading-book-select"' in response.text
    assert "Commander decision log (one per line" in response.text
    assert "Save to battle rhythm board" in response.text
    assert "Build planning cell package" in response.text
    assert "Run lone planner mode" in response.text
    assert "Build section gap cover" in response.text
    assert "Refresh MARADMIN feed" in response.text
    assert "Open second-tier watch" in response.text
    assert "Open watch lane" in response.text
    assert "Open bench / files" in response.text
    assert "Open workflows" in response.text
    assert "Run lone planner" in response.text
    assert "Watch lane" in response.text
    assert "Bench / Files lane" in response.text
    assert "Data Check" in response.text
    assert "Marine Corps History Fact" in response.text
    assert "Workflow lane" in response.text
    assert "Command Snapshots" in response.text
    assert "Start Here" in response.text
    assert "Integrated staff package" in response.text
    assert "Battle Rhythm Editor" in response.text
    assert "Act Now" in response.text
    assert "Skip to dashboard content" in response.text
    assert "dashboard.js" in response.text


def test_dashboard_assets_are_served() -> None:
    client = TestClient(app)

    response = client.get("/static/dashboard/dashboard.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_dashboard_button_inventory_has_wiring() -> None:
    html = Path("app/static/dashboard/index.html").read_text(encoding="utf-8")
    js = Path("app/static/dashboard/dashboard.js").read_text(encoding="utf-8")

    button_ids = [
        "toggle-timezone-panel",
        "load-demo",
        "load-personal",
        "refresh-maradmins",
        "refresh-reading",
        "refresh-source-watch",
        "refresh-navadmins",
        "refresh-alnavs",
        "refresh-dod-watch",
        "clear-section-memory-form",
        "quick-open-watch",
        "quick-open-library",
        "quick-open-workflows",
        "quick-run-lone-planner",
        "watch-open-workspace",
        "library-open-workspace",
        "draft-open-planning-cell",
        "draft-open-brief-clinic",
        "workflow-open-lone-planner",
        "workflow-open-planning-cell",
        "workflow-run-staff-package",
        "workflow-open-brief-clinic",
        "battle-rhythm-open-editor",
        "battle-rhythm-open-planning-cell",
        "thin-staff-run-lone-planner",
        "thin-staff-open-mission-analysis",
        "thin-staff-open-planning-cell",
        "thin-staff-open-update-cycle",
        "thin-staff-open-admin",
        "walk-in-open-lone-planner",
        "walk-in-open-brief-clinic",
        "run-lone-planner",
        "run-section-gap-cover",
        "run-staff-package",
        "save-planning-cell-board",
        "save-document-type",
        "apply-document-suggestion",
        "history-library-show-date",
        "history-library-use-today",
    ]
    for button_id in button_ids:
        assert f'id="{button_id}"' in html
        assert f'getElementById("{button_id}")' in js

    form_ids = [
        "battle-rhythm-form",
        "personnel-form",
        "staff-form",
        "brief-clinic-form",
        "uniform-photo-form",
        "staff-cycle-form",
        "planning-cell-form",
        "section-memory-form",
        "mos-advisor-form",
    ]
    for form_id in form_ids:
        assert f'id="{form_id}"' in html
        assert f'getElementById("{form_id}")' in js
        assert "addEventListener(\"submit\"" in js

    delegated_controls = [
        "data-document-id",
        "data-feed-toggle",
        "data-feed-refresh",
        "data-reading-save",
        "data-timezone-option",
    ]
    for control in delegated_controls:
        assert control in html or control in js

    assert 'id="battle-rhythm-health-posture"' in html
    assert 'id="battle-rhythm-health-summary"' in html
    assert 'id="battle-rhythm-hot-items"' in html
    assert 'renderBattleRhythmHealth(' in js
    assert 'id="section-gap-cover-output"' in html
    assert 'id="staff-package-output"' in html
    assert 'renderSectionGapCoverOutput(' in js
    assert 'renderStaffPlanningPackageOutput(' in js
    assert 'id="section-memory-library"' in html
    assert 'id="mos-bench-library"' in html
    assert 'id="reading-book-select"' in html
    assert 'id="history-library-month"' in html
    assert 'id="history-library-day"' in html
    assert 'id="history-library-summary"' in html
    assert 'id="history-library-results"' in html
    assert 'id="reference-summary"' in html
    assert 'id="reference-select"' in html
    assert 'id="document-select"' in html
    assert 'id="reference-library"' in html
    assert 'id="mos-advisor-output"' in html
    assert 'renderSectionMemoryProfile(' in js
    assert 'renderMosBenchLibrary(' in js
    assert 'renderHistoryLibrary(' in js
    assert 'renderReferenceLibrary(' in js
    assert 'renderReadingBooks(' in js
    assert 'renderAgentAdvisoryOutput(' in js
    assert 'data-section-memory-edit' in js
    assert 'data-section-memory-delete' in js
    assert 'data-section-memory-seed' in js
    assert 'data-mos-bench' in js
    assert 'id="document-type-select"' in html
    assert 'id="document-type-suggestion"' in html
    assert 'id="uniform-photo-output"' in html
    assert 'DOCUMENT_TYPE_OPTIONS' in js
    assert 'saveSelectedDocumentType(' in js
    assert 'applySuggestedDocumentType(' in js
    assert 'runUniformPhotoReview(' in js
    assert 'runStaffPlanningPackage(' in js


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
            drill_date=date(2026, 6, 6),
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
            battle_rhythm_store=battle_rhythm_store,
        )

    def override_admin() -> AdminReadinessService:
        return AdminReadinessService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
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
        assert payload["chief_brief"]["next_drill_readiness"]["anchor_drill_date"] == "2026-06-06"
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
        assert payload["alnav_ticker"][0]["status"] == "ALNAV"
        assert payload["dod_ticker"][0]["status"] == "DoD"
    finally:
        app.dependency_overrides.clear()
