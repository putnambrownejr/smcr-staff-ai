from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefBriefRequest, ChiefBriefResponse
from app.schemas.ingestion import MessageRecord
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.session import CareerTrend, FitrepReminder, PmeStatus, UserSessionHandoff
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.career.watch import CareerWatchService
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.storage.local_context_store import LocalContextStore

SEED_DIR = Path("data/seed")
DEMO_USER_KEY = "demo-smcr-officer"


def build_demo_chief_brief() -> ChiefBriefResponse:
    with TemporaryDirectory(prefix="smcr_staff_ai_demo_") as tmp_dir:
        root = Path(tmp_dir)
        context_store = LocalContextStore(root / "context")
        handoff_store = SessionHandoffStore(root / "handoffs")
        plan_store = DrillPrepPlanStore(root / "plans")
        update_store = DocumentUpdateStore(root / "updates")
        opportunity_tracker = OpportunityTracker(root / "opportunities")
        _seed_demo_context(context_store, handoff_store, plan_store, opportunity_tracker)
        orchestrator = ChiefAideOrchestrator(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            drill_plan_store=plan_store,
            reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
            document_update_store=update_store,
            opportunity_tracker=opportunity_tracker,
        )
        return orchestrator.build_brief(
            ChiefBriefRequest(
                user_key=DEMO_USER_KEY,
                maradmin_records=[
                    MessageRecord(
                        source_id="maradmin-123-26",
                        title="MARADMIN 123/26 Revision of MCO 1610.7 Performance Evaluation System",
                        canonical_url="https://example.test/maradmin-123-26",
                        published_at=datetime(2026, 5, 1, tzinfo=UTC),
                        summary="This message announces an update to FitRep/PES policy published on MCPEL.",
                    )
                ],
            )
        )


def build_demo_career_watch() -> CareerWatchResponse:
    with TemporaryDirectory(prefix="smcr_staff_ai_demo_") as tmp_dir:
        root = Path(tmp_dir)
        context_store = LocalContextStore(root / "context")
        handoff_store = SessionHandoffStore(root / "handoffs")
        opportunity_tracker = OpportunityTracker(root / "opportunities")
        _seed_demo_context(context_store, handoff_store, DrillPrepPlanStore(root / "plans"), opportunity_tracker)
        service = CareerWatchService(
            handoff_store=handoff_store,
            document_organizer=PersonalDocumentOrganizer(context_store),
            opportunity_tracker=opportunity_tracker,
            reading_catalog=ReadingListCatalogService.from_yaml(SEED_DIR / "reading_list.example.yaml"),
        )
        return service.build_watch(DEMO_USER_KEY)


def _seed_demo_context(
    context_store: LocalContextStore,
    handoff_store: SessionHandoffStore,
    plan_store: DrillPrepPlanStore,
    opportunity_tracker: OpportunityTracker,
) -> None:
    bio_item = context_store.save(
        filename="demo-bio.txt",
        content=b"Capt Example Smith, 0602 communications officer bio draft.",
        content_type="text/plain",
        document_type="bio",
        tags=["demo", "career"],
        consent_ack=True,
    )
    rqs_item = context_store.save(
        filename="demo-rqs.txt",
        content=b"Demo reserve qualification summary reference.",
        content_type="text/plain",
        document_type="rqs",
        tags=["demo", "career"],
        consent_ack=True,
    )
    handoff_store.upsert(
        UserSessionHandoff(
            user_key=DEMO_USER_KEY,
            display_name="Capt Demo Smith",
            rank="Capt",
            mos="0602",
            billet="CommO",
            pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 6, 1))],
            fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15), role="MRO")],
            admin_watch_items=["DTS voucher after drill", "Confirm annual medical readiness status"],
            recurring_drill_notes=["Every drill confirm uniform, haircut, and laptop kit."],
            rqs_context_id=rqs_item.context_id,
            bio_context_id=bio_item.context_id,
            career_trends=[
                CareerTrend(
                    label="Broadening assignment interest",
                    direction="watch",
                    evidence=["User is exploring reserve planning and ADOS opportunities."],
                    recommended_action="Review one ADOS and one SMCR BIC opportunity before next drill.",
                )
            ],
            recommended_courses=["MarineNet writing refresher", "Reserve admin fundamentals"],
        )
    )
    plan_store.save(
        DrillPrepPlanResponse(
            id="demo-drill-plan",
            drill_date=date(2026, 6, 6),
            tasks=[
                PrepTask(title="Pack gear", due_offset_days=3, due_date=date(2026, 6, 3), category="gear"),
                PrepTask(
                    title="Confirm travel and DTS status",
                    due_offset_days=5,
                    due_date=date(2026, 6, 1),
                    category="travel",
                ),
            ],
        )
    )
    opportunity_tracker.track(
        [
            ManualOpportunityRequest(
                title="Communications Officer",
                opportunity_type="smcr_bic",
                unit="6th Comm Bn",
                location="New Orleans, LA",
                mos="0602",
                rank="Capt",
                source_url="https://example.test/bic",
                description="Reserve communications planning billet.",
                due_date=date(2026, 6, 20),
            ),
            ManualOpportunityRequest(
                title="ADOS Planner",
                opportunity_type="ados",
                unit="4th MLG",
                location="Remote",
                mos="0502",
                rank="Capt",
                source_url="https://example.test/ados",
                description="Temporary planning support assignment.",
                due_date=date(2026, 6, 18),
            ),
        ]
    )
