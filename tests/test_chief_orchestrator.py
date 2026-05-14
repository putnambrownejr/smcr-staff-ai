from datetime import UTC, date, datetime
from pathlib import Path

from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.chief import ChiefBriefRequest
from app.schemas.ingestion import MessageRecord
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.session import CareerTrend, FitrepReminder, PmeStatus, UserSessionHandoff
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateReviewStatus
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
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
