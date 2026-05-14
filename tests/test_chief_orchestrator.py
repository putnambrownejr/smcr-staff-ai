from datetime import UTC, date, datetime
from pathlib import Path

from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.chief import ChiefBriefRequest
from app.schemas.ingestion import MessageRecord
from app.schemas.session import FitrepReminder, PmeStatus, UserSessionHandoff
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
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
