from datetime import UTC, date, datetime
from pathlib import Path

from app.schemas.battle_rhythm import BattleRhythmBoardUpsertRequest, BattleRhythmEntryInput
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.chief import ChiefBriefRequest
from app.schemas.connector_digest import TravelEmailCaseSummary
from app.schemas.ingestion import MessageRecord
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.session import (
    CareerTrend,
    DrillDateRecord,
    FitrepReminder,
    PmeStatus,
    RecurringCheck,
    UserSessionHandoff,
)
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateReviewStatus
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.storage.local_context_store import LocalContextStore


def test_chief_brief_combines_handoff_docs_drill_and_updates(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    context_store.save(
        filename="bio.txt",
        content=b"BIO draft with phone: 555-123-4567",
        content_type="text/plain",
        document_type="bio",
    )
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-example",
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 6, 1))],
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 30))],
            admin_watch_items=["DTS voucher after drill"],
            recommended_courses=["MarineNet writing refresher"],
            career_trends=[CareerTrend(label="Broaden planning exposure")],
        )
    )
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    plan_store.save(
        DrillPrepPlanResponse(
            id="drill-test",
            drill_date=date(2026, 6, 6),
            tasks=[
                PrepTask(
                    title="Pack gear",
                    due_offset_days=3,
                    due_date=date(2026, 6, 3),
                    category="gear",
                )
            ],
        )
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=plan_store,
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )
    battle_rhythm_store = BattleRhythmStore(tmp_path / "battle-rhythm")
    battle_rhythm_store.upsert(
        "capt-example",
        BattleRhythmBoardUpsertRequest(
            board_title="Drill board",
            assumption_log=[BattleRhythmEntryInput(text="Transport remains supportable.", section="S-4")],
            commander_decision_log=[BattleRhythmEntryInput(text="Approve the final lane mix.", section="Command")],
            due_out_board=[BattleRhythmEntryInput(text="S-6: Confirm reporting method.", section="S-6")],
            next_touchpoint="Before final drill sync.",
        ),
    )
    orchestrator.battle_rhythm_store = battle_rhythm_store

    brief = orchestrator.build_brief(
        ChiefBriefRequest(
            user_key="capt-example",
            maradmin_records=[
                MessageRecord(
                    source_id="maradmin-123-26",
                    title="MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
                    canonical_url="https://example.test/maradmin",
                    published_at=datetime(2026, 5, 1, tzinfo=UTC),
                    summary="This message announces an update to FitRep/PES policy published on MCPEL.",
                )
            ],
        )
    )

    categories = {item.category for item in brief.action_items}
    assert {"pme", "fitrep", "admin", "documents", "drill", "source_updates"}.issubset(categories)
    assert brief.document_summary is not None
    assert brief.document_summary.pii_flagged_count == 1
    assert brief.documentation_updates
    assert brief.reading_recommendations
    assert brief.recommended_courses
    assert brief.summary_lines
    assert brief.top_priority_items
    assert brief.next_drill_readiness.anchor_drill_date == date(2026, 6, 6)
    assert brief.next_drill_readiness.must_do_before_drill
    assert brief.next_drill_readiness.decisive_action
    assert brief.next_drill_readiness.this_week_focus
    assert brief.next_drill_readiness.ready_if
    assert brief.next_drill_readiness.recommended_follow_on_workflows
    assert "POST /staff/update-cycle" in brief.next_drill_readiness.recommended_follow_on_workflows
    assert brief.thin_staff_assist.walk_in_brief
    assert brief.thin_staff_assist.missing_section_questions
    assert brief.thin_staff_assist.recommended_products
    assert brief.thin_staff_assist.next_touchpoint
    assert brief.battle_rhythm_summary
    assert brief.battle_rhythm is not None


def test_chief_brief_flags_stale_handoff_and_missing_core_docs(tmp_path: Path) -> None:
    context_store = LocalContextStore(tmp_path / "context")
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-stale",
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 5, 20))],
        )
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(context_store),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key="capt-stale"))

    assert brief.handoff_is_stale is True
    assert any("stale" in warning.lower() for warning in brief.warnings)
    titles = {item.title for item in brief.action_items}
    assert "Add RQS reference" in titles
    assert "Add a current BIO reference" in titles
    assert "Add current orders reference" in titles


def test_chief_brief_uses_persisted_document_updates_and_skips_ignored(tmp_path: Path) -> None:
    update_store = DocumentUpdateStore(tmp_path / "updates")
    update_store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="update-new",
                tracked_title="PES / FitRep",
                trigger_type="maradmin",
                review_status=UpdateReviewStatus.new,
            ),
            DocumentationUpdateCandidate(
                candidate_id="update-ignored",
                tracked_title="Uniform Regulations",
                trigger_type="maradmin",
                review_status=UpdateReviewStatus.ignored,
            ),
        ]
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(tmp_path / "handoffs"),
        document_organizer=PersonalDocumentOrganizer(LocalContextStore(tmp_path / "context")),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=update_store,
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key=None))

    update_titles = [item.title for item in brief.action_items if item.category == "source_updates"]
    assert "Source update (new): PES / FitRep" in update_titles
    assert all("Uniform Regulations" not in title for title in update_titles)


def test_chief_brief_surfaces_tracked_career_opportunities(tmp_path: Path) -> None:
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")
    opportunity_tracker.track(
        [
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                location="Remote",
                rank="Capt",
                due_date=date(2026, 6, 15),
            )
        ]
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(tmp_path / "handoffs"),
        document_organizer=PersonalDocumentOrganizer(LocalContextStore(tmp_path / "context")),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=opportunity_tracker,
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key=None))

    career_titles = [item.title for item in brief.action_items if item.category == "career"]
    assert "Career opportunity (ados): ADOS Planner" in career_titles


def test_chief_brief_dedupes_and_prioritizes_digest_items(tmp_path: Path) -> None:
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-digest",
            updated_at=datetime(2026, 5, 10, tzinfo=UTC),
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 5, 18))],
            recommended_courses=["MarineNet writing refresher", "MarineNet writing refresher"],
            career_trends=[
                CareerTrend(
                    label="Broadening assignment interest",
                    recommended_action="Review ADOS opportunities before next drill.",
                )
            ],
        )
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(LocalContextStore(tmp_path / "context")),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key="capt-digest"))

    assert brief.summary_lines
    assert brief.top_priority_items
    assert len(brief.recommended_courses) == 2
    course_titles = [item.title for item in brief.action_items if item.title.startswith("Course recommendation:")]
    assert len(course_titles) == 1


def test_chief_brief_surfaces_recurring_checks_and_drill_schedule(tmp_path: Path) -> None:
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-rhythm",
            updated_at=datetime(2026, 5, 10, tzinfo=UTC),
            drill_dates=[DrillDateRecord(drill_date=date(2026, 6, 6), label="June drill")],
            recurring_drill_notes=["Every drill confirm uniform and haircut."],
            recurring_checks=[
                RecurringCheck(
                    title="After drill review DTS voucher and close travel-admin loose ends.",
                    cadence="post_drill",
                    category="travel",
                    due_offset_days=3,
                ),
                RecurringCheck(
                    title="Monthly review myPay and TSP allocations.",
                    cadence="monthly",
                    category="finance",
                ),
            ],
        )
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(LocalContextStore(tmp_path / "context")),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key="capt-rhythm"))

    titles = {item.title for item in brief.action_items}
    assert "Recurring drill reminder: Every drill confirm uniform and haircut." in titles
    assert "Recurring travel check: After drill review DTS voucher and close travel-admin loose ends." in titles
    assert "Recurring finance check: Monthly review myPay and TSP allocations." in titles
    assert any("recurring readiness/admin check" in line for line in brief.summary_lines)
    assert any("travel-admin" in item.lower() for item in brief.next_drill_readiness.likely_friction_points)
    assert brief.next_drill_readiness.decisive_action
    assert brief.next_drill_readiness.this_week_focus


def test_chief_brief_reads_stored_travel_cases(tmp_path: Path) -> None:
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    handoff_store.upsert(UserSessionHandoff(user_key="capt-travel-watch"))
    travel_case_store = TravelCaseStore(tmp_path / "travel-cases")
    travel_case_store.upsert_many(
        "capt-travel-watch",
        [
            TravelEmailCaseSummary(
                title="CI Travel itinerary",
                source_subject="CI Travel itinerary",
                sender="noreply@citravel.example",
                message_received_at=datetime(2026, 6, 1, 14, 30, tzinfo=UTC),
                travel_status="post_travel",
                travel_start=date(2026, 6, 6),
                travel_end=date(2026, 6, 8),
                voucher_due_date=date(2026, 6, 13),
                rental_car_expected=True,
                receipts_to_collect=["lodging", "rental car"],
                attached_receipt_categories=["lodging"],
                attachment_names=["Hilton_folio.pdf"],
                attachment_follow_up_prompts=["Still collect or upload locally: rental car."],
            )
        ],
    )
    orchestrator = ChiefAideOrchestrator(
        handoff_store=handoff_store,
        document_organizer=PersonalDocumentOrganizer(LocalContextStore(tmp_path / "context")),
        drill_plan_store=DrillPrepPlanStore(tmp_path / "plans"),
        reading_catalog=ReadingListCatalogService.from_yaml(Path("data/seed/reading_list.example.yaml")),
        document_update_store=DocumentUpdateStore(tmp_path / "updates"),
        opportunity_tracker=OpportunityTracker(tmp_path / "opportunities"),
        travel_case_store=travel_case_store,
    )

    brief = orchestrator.build_brief(ChiefBriefRequest(user_key="capt-travel-watch"))

    assert brief.travel_cases
    assert any(item.category == "travel" for item in brief.action_items)
    assert any("attachments" in item.title.lower() for item in brief.action_items)
    assert any("stored travel case" in line.lower() for line in brief.summary_lines)
