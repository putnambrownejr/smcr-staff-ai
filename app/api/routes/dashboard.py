from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.actions import ActionRecord, ActionStatus
from app.schemas.admin import AdminReadinessResponse
from app.schemas.battle_rhythm import BattleRhythmBoardResponse
from app.schemas.career import CareerWatchResponse
from app.schemas.chief import ChiefActionItem, ChiefBriefRequest, ChiefBriefResponse
from app.schemas.custom_watch_feeds import CustomWatchFeed
from app.schemas.dashboard import (
    AnalystBrief,
    DailyOpsBrief,
    DailyOpsEntry,
    DashboardCustomWatchFeed,
    DashboardDocumentDetail,
    DashboardReadingBook,
    DashboardReferenceEntry,
    DashboardReferenceLink,
    DashboardTemplateReference,
    DashboardTickerItem,
    DashboardWorkspaceResponse,
)
from app.schemas.history import TodayInMarineHistoryItem
from app.schemas.ingestion import MessageRecord
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.reading_state import ReadingProgressRecord
from app.schemas.section_memory import SectionMemoryProfile
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateReviewStatus
from app.services.actions.tracker import ActionTracker
from app.services.admin.readiness import AdminReadinessService
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.career.watch import CareerWatchService
from app.services.chief.orchestrator import ChiefAideOrchestrator
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.demo.scenarios import DEMO_USER_KEY, build_demo_career_watch, build_demo_chief_brief
from app.services.documents.personal_document_organizer import PersonalDocumentOrganizer
from app.services.history.today_in_history import TodayInMarineHistoryService
from app.services.ingestion.custom_watch_feed_store import CustomWatchFeedStore
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.ingestion.maradmin_feed_service import MaradminFeedService
from app.services.ingestion.maradmin_feed_store import MaradminFeedStore
from app.services.ingestion.message_record_store import MessageRecordStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.reading.catalog_store import ReadingListCatalogStore
from app.services.reading.live_catalog import load_effective_reading_catalog
from app.services.reading.state_store import ReadingProgressStore
from app.services.session.handoff_store import SessionHandoffStore
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.staff.section_memory_store import SectionMemoryStore
from app.services.storage.local_context_store import LocalContextStore
from app.services.templates.product_template_repository import ProductTemplateRepository
from app.services.templates.system_template_catalog import SystemTemplateCatalog

router = APIRouter(tags=["dashboard"])
_DASHBOARD_HTML = Path(__file__).resolve().parents[2] / "static" / "dashboard" / "index.html"
SEED_DIR = Path("data/seed")
_reference_library_cache: list[DashboardReferenceEntry] | None = None


@router.get("/dashboard", summary="Open the lightweight SMCR Staff AI dashboard")
def get_dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD_HTML)


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


def get_document_organizer(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> PersonalDocumentOrganizer:
    return PersonalDocumentOrganizer(store)


def get_chief_orchestrator(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> ChiefAideOrchestrator:
    settings = get_settings()
    return ChiefAideOrchestrator(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        drill_plan_store=DrillPrepPlanStore(f"{settings.local_context_storage_dir}/drill_plans"),
        reading_catalog=load_effective_reading_catalog(
            seed_path=SEED_DIR / "reading_list.example.yaml",
            store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
        ),
        document_update_store=DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates"),
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
        travel_case_store=TravelCaseStore(settings.travel_case_storage_dir),
        battle_rhythm_store=BattleRhythmStore(settings.battle_rhythm_storage_dir),
    )


def get_admin_service(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> AdminReadinessService:
    settings = get_settings()
    return AdminReadinessService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        travel_case_store=TravelCaseStore(settings.travel_case_storage_dir),
    )


def get_career_service(
    store: Annotated[LocalContextStore, Depends(get_context_store)],
) -> CareerWatchService:
    settings = get_settings()
    return CareerWatchService(
        handoff_store=SessionHandoffStore(settings.session_handoff_storage_dir),
        document_organizer=PersonalDocumentOrganizer(store),
        opportunity_tracker=OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities"),
        reading_catalog=load_effective_reading_catalog(
            seed_path=SEED_DIR / "reading_list.example.yaml",
            store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
        ),
        reading_state_store=ReadingProgressStore(settings.reading_state_storage_dir),
    )


def get_opportunity_tracker() -> Iterator[OpportunityTracker]:
    settings = get_settings()
    yield OpportunityTracker(f"{settings.local_context_storage_dir}/opportunities")


def get_update_store() -> Iterator[DocumentUpdateStore]:
    settings = get_settings()
    yield DocumentUpdateStore(f"{settings.local_context_storage_dir}/document_updates")


def get_action_tracker() -> Iterator[ActionTracker]:
    settings = get_settings()
    yield ActionTracker(f"{settings.local_context_storage_dir}/actions")


def get_battle_rhythm_store() -> Iterator[BattleRhythmStore]:
    settings = get_settings()
    yield BattleRhythmStore(settings.battle_rhythm_storage_dir)


def get_section_memory_store() -> Iterator[SectionMemoryStore]:
    settings = get_settings()
    yield SectionMemoryStore(settings.section_memory_storage_dir)


def get_template_repository() -> Iterator[ProductTemplateRepository]:
    settings = get_settings()
    yield ProductTemplateRepository(settings.product_template_storage_dir)


def get_system_template_catalog() -> SystemTemplateCatalog:
    return SystemTemplateCatalog.from_yaml(SEED_DIR / "system_templates.example.yaml")


def get_reading_state_store() -> Iterator[ReadingProgressStore]:
    settings = get_settings()
    yield ReadingProgressStore(settings.reading_state_storage_dir)


def get_reading_catalog_service() -> ReadingListCatalogService:
    settings = get_settings()
    return load_effective_reading_catalog(
        seed_path=SEED_DIR / "reading_list.example.yaml",
        store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
    )


def get_maradmin_feed_store() -> Iterator[MaradminFeedStore]:
    settings = get_settings()
    yield MaradminFeedStore(settings.maradmin_feed_storage_dir)


def get_maradmin_feed_service() -> MaradminFeedService:
    return MaradminFeedService()


def get_navadmin_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(Path(settings.navy_message_storage_dir) / "navadmins")


def get_alnav_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(Path(settings.navy_message_storage_dir) / "alnavs")


def get_dod_watch_store() -> Iterator[MessageRecordStore]:
    settings = get_settings()
    yield MessageRecordStore(settings.dod_watch_storage_dir)


def get_history_service() -> TodayInMarineHistoryService:
    settings = get_settings()
    local_history_path = Path(settings.history_storage_dir) / "today_in_history.yaml"
    return TodayInMarineHistoryService.from_paths(
        [
            SEED_DIR / "usmc_history_on_this_day.example.yaml",
            local_history_path,
        ]
    )


def get_custom_watch_feed_store() -> Iterator[CustomWatchFeedStore]:
    settings = get_settings()
    yield CustomWatchFeedStore(settings.custom_watch_feed_storage_dir)


@router.get(
    "/dashboard/data/{user_key}",
    response_model=DashboardWorkspaceResponse,
    dependencies=[LocalApiKeyDependency],
    summary="Load a consolidated personal dashboard workspace payload",
)
def get_dashboard_data(
    user_key: str,
    orchestrator: Annotated[ChiefAideOrchestrator, Depends(get_chief_orchestrator)],
    admin_service: Annotated[AdminReadinessService, Depends(get_admin_service)],
    career_service: Annotated[CareerWatchService, Depends(get_career_service)],
    organizer: Annotated[PersonalDocumentOrganizer, Depends(get_document_organizer)],
    action_tracker: Annotated[ActionTracker, Depends(get_action_tracker)],
    battle_rhythm_store: Annotated[BattleRhythmStore, Depends(get_battle_rhythm_store)],
    section_memory_store: Annotated[SectionMemoryStore, Depends(get_section_memory_store)],
    opportunity_tracker: Annotated[OpportunityTracker, Depends(get_opportunity_tracker)],
    update_store: Annotated[DocumentUpdateStore, Depends(get_update_store)],
    template_repository: Annotated[ProductTemplateRepository, Depends(get_template_repository)],
    system_template_catalog: Annotated[SystemTemplateCatalog, Depends(get_system_template_catalog)],
    reading_state_store: Annotated[ReadingProgressStore, Depends(get_reading_state_store)],
    reading_catalog: Annotated[ReadingListCatalogService, Depends(get_reading_catalog_service)],
    maradmin_feed_store: Annotated[MaradminFeedStore, Depends(get_maradmin_feed_store)],
    navadmin_store: Annotated[MessageRecordStore, Depends(get_navadmin_store)],
    alnav_store: Annotated[MessageRecordStore, Depends(get_alnav_store)],
    dod_watch_store: Annotated[MessageRecordStore, Depends(get_dod_watch_store)],
    custom_watch_feed_store: Annotated[CustomWatchFeedStore, Depends(get_custom_watch_feed_store)],
    history_service: Annotated[TodayInMarineHistoryService, Depends(get_history_service)],
) -> DashboardWorkspaceResponse:
    chief_brief = orchestrator.build_brief(ChiefBriefRequest(user_key=user_key))
    admin_readiness = admin_service.build(user_key)
    career_watch = career_service.build_watch(user_key)
    document_summary = organizer.list_documents()
    battle_rhythm = battle_rhythm_store.get(user_key)
    section_memory_profile = section_memory_store.get(user_key)
    tracked_actions = action_tracker.list(user_key=user_key, include_closed=False)[:12]
    tracked_opportunities = list(opportunity_tracker.list())[:8]
    documentation_updates = [
        item for item in update_store.list() if item.review_status != UpdateReviewStatus.ignored
    ][:8]
    maradmin_feed = maradmin_feed_store.list(limit=10)
    custom_watch_feeds = _custom_watch_feed_summaries(custom_watch_feed_store)
    reading_progress = {item.slug: item for item in reading_state_store.list(user_key).records}
    history_library = history_service.list_items()
    return _workspace_response(
        mode="personal",
        user_key=user_key,
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        battle_rhythm=battle_rhythm,
        document_summary=document_summary,
        tracked_actions=tracked_actions,
        tracked_opportunities=tracked_opportunities,
        documentation_updates=documentation_updates,
        document_details=_document_details(organizer),
        template_library=_template_library(
            system_template_catalog=system_template_catalog,
            template_repository=template_repository,
        ),
        section_memory_profile=section_memory_profile,
        maradmin_ticker=_maradmin_ticker(maradmin_feed),
        navadmin_ticker=_message_watch_ticker(navadmin_store.list(limit=8)),
        alnav_ticker=_message_watch_ticker(alnav_store.list(limit=8)),
        dod_ticker=_message_watch_ticker(dod_watch_store.list(limit=8)),
        custom_watch_feeds=custom_watch_feeds,
        today_in_history=history_service.get_for_date(datetime.now(UTC).date()),
        history_library=history_library,
        reference_library=_reference_library(),
        reading_books=_reading_books(
            reading_catalog=reading_catalog,
            reading_progress=reading_progress,
        ),
    )


@router.get(
    "/demo/dashboard/data",
    response_model=DashboardWorkspaceResponse,
    summary="Load a consolidated stateless demo dashboard payload",
)
def get_demo_dashboard_data() -> DashboardWorkspaceResponse:
    chief_brief = build_demo_chief_brief()
    career_watch = build_demo_career_watch()
    admin_readiness = _admin_from_demo_brief(chief_brief)
    settings = get_settings()
    maradmin_feed = MaradminFeedStore(settings.maradmin_feed_storage_dir).list(limit=10)
    navadmin_feed = MessageRecordStore(Path(settings.navy_message_storage_dir) / "navadmins").list(limit=8)
    alnav_feed = MessageRecordStore(Path(settings.navy_message_storage_dir) / "alnavs").list(limit=8)
    dod_feed = MessageRecordStore(settings.dod_watch_storage_dir).list(limit=8)
    custom_watch_feeds = _custom_watch_feed_summaries(
        CustomWatchFeedStore(settings.custom_watch_feed_storage_dir)
    )
    history_service = get_history_service()
    reading_catalog = load_effective_reading_catalog(
        seed_path=SEED_DIR / "reading_list.example.yaml",
        store=ReadingListCatalogStore(settings.reading_catalog_storage_dir),
    )
    demo_battle_rhythm = _demo_battle_rhythm(chief_brief)
    return _workspace_response(
        mode="demo",
        user_key=DEMO_USER_KEY,
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        battle_rhythm=demo_battle_rhythm,
        document_summary=chief_brief.document_summary,
        tracked_actions=[],
        tracked_opportunities=career_watch.tracked_opportunities,
        documentation_updates=chief_brief.documentation_updates,
        document_details=[],
        template_library=_template_library(
            system_template_catalog=SystemTemplateCatalog.from_yaml(SEED_DIR / "system_templates.example.yaml"),
            template_repository=None,
        ),
        section_memory_profile=None,
        maradmin_ticker=_maradmin_ticker(maradmin_feed),
        navadmin_ticker=_message_watch_ticker(navadmin_feed),
        alnav_ticker=_message_watch_ticker(alnav_feed),
        dod_ticker=_message_watch_ticker(dod_feed),
        custom_watch_feeds=custom_watch_feeds,
        today_in_history=history_service.get_for_date(datetime.now(UTC).date()),
        history_library=history_service.list_items(),
        reference_library=_reference_library(),
        reading_books=_reading_books(
            reading_catalog=reading_catalog,
            reading_progress={},
        ),
    )


def _workspace_response(
    *,
    mode: str,
    user_key: str | None,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    battle_rhythm: BattleRhythmBoardResponse | None,
    document_summary: PersonalDocumentSummary | None,
    tracked_actions: list[ActionRecord],
    tracked_opportunities: list[OpportunityRecord],
    documentation_updates: list[DocumentationUpdateCandidate],
    document_details: list[DashboardDocumentDetail],
    template_library: list[DashboardTemplateReference],
    section_memory_profile: SectionMemoryProfile | None,
    maradmin_ticker: list[DashboardTickerItem],
    navadmin_ticker: list[DashboardTickerItem],
    alnav_ticker: list[DashboardTickerItem],
    dod_ticker: list[DashboardTickerItem],
    custom_watch_feeds: list[DashboardCustomWatchFeed],
    today_in_history: list[TodayInMarineHistoryItem],
    history_library: list[TodayInMarineHistoryItem],
    reference_library: list[DashboardReferenceEntry],
    reading_books: list[DashboardReadingBook],
) -> DashboardWorkspaceResponse:
    summary_lines = [
        *chief_brief.next_drill_readiness.summary[:2],
        *chief_brief.summary_lines[:2],
        *admin_readiness.summary_lines[:1],
        *career_watch.warnings[:1],
    ]
    warnings = list(dict.fromkeys([
        *chief_brief.warnings,
        *admin_readiness.warnings,
        *career_watch.warnings,
    ]))
    return DashboardWorkspaceResponse(
        mode=mode,
        user_key=user_key,
        summary_lines=[line for line in summary_lines if line],
        chief_brief=chief_brief,
        admin_readiness=admin_readiness,
        career_watch=career_watch,
        battle_rhythm=battle_rhythm,
        daily_ops_brief=_daily_ops_brief(
            chief_brief=chief_brief,
            admin_readiness=admin_readiness,
            career_watch=career_watch,
            tracked_actions=tracked_actions,
            documentation_updates=documentation_updates,
            document_summary=document_summary,
        ),
        analyst_brief=_analyst_brief(
            chief_brief=chief_brief,
            admin_readiness=admin_readiness,
            career_watch=career_watch,
            documentation_updates=documentation_updates,
            tracked_actions=tracked_actions,
            tracked_opportunities=tracked_opportunities,
            document_summary=document_summary,
        ),
        document_summary=document_summary,
        tracked_actions=tracked_actions,
        tracked_opportunities=tracked_opportunities,
        documentation_updates=documentation_updates,
        document_details=document_details,
        template_library=template_library,
        section_memory_profile=section_memory_profile,
        maradmin_ticker=maradmin_ticker,
        navadmin_ticker=navadmin_ticker,
        alnav_ticker=alnav_ticker,
        dod_ticker=dod_ticker,
        custom_watch_feeds=custom_watch_feeds,
        today_in_history=today_in_history,
        history_library=history_library,
        reference_library=reference_library,
        reading_books=reading_books,
        warnings=warnings,
    )


def _document_details(organizer: PersonalDocumentOrganizer) -> list[DashboardDocumentDetail]:
    entries: list[DashboardDocumentDetail] = []
    for detail in (
        organizer.get_document(record.context_id)
        for record in organizer.list_documents().records[:8]
    ):
        if detail is None:
            continue
        suggestion = organizer.suggest_document_type(detail)
        entries.append(
            DashboardDocumentDetail(
                context_id=detail.record.context_id,
                filename=detail.record.filename,
                document_type=detail.record.document_type.value,
                suggested_document_type=suggestion[0] if suggestion else None,
                suggestion_reason=suggestion[1] if suggestion else None,
                contains_pii=detail.record.contains_pii,
                review_date=detail.record.review_date.isoformat() if detail.record.review_date else None,
                expiration_date=detail.record.expiration_date.isoformat() if detail.record.expiration_date else None,
                text_preview=detail.text_preview,
            )
        )
    return entries


def _template_library(
    *,
    system_template_catalog: SystemTemplateCatalog,
    template_repository: ProductTemplateRepository | None,
) -> list[DashboardTemplateReference]:
    system_templates = [
        DashboardTemplateReference(
            template_id=record.template_id,
            template_name=record.template_name,
            template_type=record.template_type.value,
            template_source="system",
            description=record.description,
            tags=record.tags,
            preferred_format=record.preferred_format,
            reusable_headings=record.reusable_headings,
            reusable_guidance=record.reusable_guidance,
            warnings=record.warnings,
        )
        for record in system_template_catalog.list()
    ]
    local_templates: list[DashboardTemplateReference] = []
    if template_repository is not None:
        local_templates = [
            DashboardTemplateReference(
                template_id=record.template_id,
                template_name=record.template_name,
                template_type=record.template_type.value,
                template_source="user",
                description=record.description,
                tags=record.tags,
                preferred_format=record.preferred_format,
                reusable_headings=record.reusable_headings,
                reusable_guidance=record.reusable_guidance,
                warnings=record.warnings,
            )
            for record in template_repository.list()[:10]
        ]
    return [*local_templates, *system_templates]


def _maradmin_ticker(records: list[MessageRecord]) -> list[DashboardTickerItem]:
    return [
        DashboardTickerItem(
            title=item.title,
            status=item.status,
            summary=(
                ", ".join(item.tags[:3])
                or item.summary
                or "Live MARADMIN feed item."
            )[:220],
            source_url=item.canonical_url,
        )
        for item in records[:8]
    ]


def _custom_watch_feed_summaries(store: CustomWatchFeedStore) -> list[DashboardCustomWatchFeed]:
    return [_custom_watch_feed_summary(feed, store) for feed in store.list()[:8]]


def _message_watch_ticker(records: list[MessageRecord]) -> list[DashboardTickerItem]:
    return [
        DashboardTickerItem(
            title=item.title,
            status=item.source_family,
            summary=(item.summary or ", ".join(item.tags[:3]) or "Second-tier message-watch item.")[:220],
            source_url=item.canonical_url,
        )
        for item in records[:8]
    ]


def _custom_watch_feed_summary(feed: CustomWatchFeed, store: CustomWatchFeedStore) -> DashboardCustomWatchFeed:
    item_store = MessageRecordStore(store.items_path(feed.feed_id))
    previews = [
        DashboardTickerItem(
            title=item.title,
            status=item.status,
            summary=(item.summary or ", ".join(item.tags[:3]) or "Custom watch item.")[:220],
            source_url=item.canonical_url,
        )
        for item in item_store.list(limit=3)
    ]
    return DashboardCustomWatchFeed(
        feed_id=feed.feed_id,
        name=feed.name,
        category=feed.category,
        trust_level=feed.trust_level,
        enabled=feed.enabled,
        last_refreshed_at=feed.last_refreshed_at.isoformat() if feed.last_refreshed_at else None,
        last_error=feed.last_error,
        last_item_count=feed.last_item_count,
        tags=feed.tags,
        preview_items=previews,
    )


def _reading_books(
    *,
    reading_catalog: ReadingListCatalogService,
    reading_progress: dict[str, ReadingProgressRecord],
) -> list[DashboardReadingBook]:
    books = reading_catalog.list_books()[:12]
    return [
        DashboardReadingBook(
            slug=book.slug,
            title=book.title,
            author=book.author,
            categories=book.categories,
            open_source_available=book.open_source_available,
            summary=book.summary,
            key_themes=book.key_themes,
            source_urls=book.source_urls,
            progress=reading_progress.get(book.slug),
        )
        for book in books
    ]


def _reference_library() -> list[DashboardReferenceEntry]:
    global _reference_library_cache
    if _reference_library_cache is not None:
        return _reference_library_cache
    source_dir = Path("docs/sources")
    if not source_dir.exists():
        return []
    entries = [
        _reference_entry_from_file(path)
        for path in sorted(source_dir.glob("*.md"))
        if path.name.lower() != "readme.md"
    ]
    _reference_library_cache = [entry for entry in entries if entry is not None]
    return _reference_library_cache


def _reference_entry_from_file(path: Path) -> DashboardReferenceEntry | None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = next((line.removeprefix("#").strip() for line in lines if line.startswith("# ")), "")
    if not title:
        return None
    summary = _extract_reference_summary(lines)
    official_links = _extract_reference_links(lines)
    return DashboardReferenceEntry(
        slug=path.stem,
        title=title,
        summary=summary or "Curated source note for staff reference and future grounding.",
        note_path=path.as_posix(),
        official_links=official_links[:6],
    )


def _extract_reference_summary(lines: list[str]) -> str:
    summary_parts: list[str] = []
    capture = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if capture and summary_parts:
                break
            continue
        if stripped.startswith("# "):
            capture = True
            continue
        if not capture:
            continue
        if stripped.startswith("## ") or stripped.startswith("- "):
            break
        summary_parts.append(stripped)
    return " ".join(summary_parts).strip()


def _extract_reference_links(lines: list[str]) -> list[DashboardReferenceLink]:
    links: list[DashboardReferenceLink] = []
    current_title = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- Title: "):
            current_title = stripped.removeprefix("- Title: ").strip()
            continue
        if (
            stripped.startswith("- ")
            and not stripped.startswith("- Title: ")
            and not stripped.startswith("- Type: ")
            and not stripped.startswith("- Category: ")
            and not stripped.startswith("- Notes: ")
            and not stripped.startswith("- Why it matters: ")
            and not stripped.startswith("- Classification label: ")
            and not stripped.startswith("- CUI flag: ")
            and not stripped.startswith("- Official URL: ")
            and not stripped.startswith("- URL: ")
            and not stripped.startswith("- Current strategy page: ")
            and not stripped.startswith("- Public-domain text: ")
            and not stripped.startswith("- Public-domain translation: ")
            and not stripped.startswith("- Official public PDF: ")
            and "http" not in stripped
        ):
            current_title = stripped.removeprefix("- ").strip()
            continue
        if stripped.startswith("- Official URL: "):
            url = stripped.removeprefix("- Official URL: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("- URL: "):
            url = stripped.removeprefix("- URL: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("- Current strategy page: "):
            url = stripped.removeprefix("- Current strategy page: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("- Public-domain text: "):
            url = stripped.removeprefix("- Public-domain text: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("- Public-domain translation: "):
            url = stripped.removeprefix("- Public-domain translation: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("- Official public PDF: "):
            url = stripped.removeprefix("- Official public PDF: ").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
            continue
        if stripped.startswith("url:"):
            url = stripped.removeprefix("url:").strip()
            if current_title and url:
                links.append(DashboardReferenceLink(title=current_title, url=url))
    deduped: list[DashboardReferenceLink] = []
    seen: set[tuple[str, str]] = set()
    for link in links:
        key = (link.title, link.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(link)
    return deduped


def _admin_from_demo_brief(chief_brief: ChiefBriefResponse) -> AdminReadinessResponse:
    document_summary = chief_brief.document_summary
    items = []
    for item in chief_brief.action_items:
        if item.category in {"admin", "fitrep", "documents", "travel"}:
            items.append(
                {
                    "title": item.title,
                    "category": item.category,
                    "priority": item.priority,
                    "due_date": item.due_date,
                    "recommendation": item.recommendation,
                    "source": item.source,
                }
            )
    return AdminReadinessResponse(
        title="Demo admin readiness",
        user_key=DEMO_USER_KEY,
        handoff=chief_brief.handoff,
        summary_lines=[
            "Demo mode shows a synthesized admin slice derived from the Chief/Aide brief.",
            "Use personal mode for real local document, travel, and readiness cues.",
        ],
        items=items[:6],
        document_summary=document_summary,
        warnings=["Demo mode is stateless and read-only."],
    )


def _demo_battle_rhythm(chief_brief: ChiefBriefResponse) -> BattleRhythmBoardResponse:
    return BattleRhythmBoardResponse(
        user_key=DEMO_USER_KEY,
        board_title="Demo battle rhythm board",
        source_title="Demo planning cell",
        focus=chief_brief.summary_lines[:3],
        assumption_log=[],
        commander_decision_log=[],
        question_log=[],
        due_out_board=[],
        next_touchpoint=chief_brief.thin_staff_assist.next_touchpoint,
        context_note="Demo mode shows the shape of the continuity board without persisting personal staff data.",
        warnings=["Demo mode is read-only."],
    )


def _daily_ops_brief(
    *,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    documentation_updates: list[DocumentationUpdateCandidate],
    tracked_actions: list[ActionRecord],
    document_summary: PersonalDocumentSummary | None,
) -> DailyOpsBrief:
    actions = chief_brief.action_items
    must_do = [_entry_from_action(item) for item in actions if item.priority == "high"][:5]
    if not must_do:
        must_do = [_entry_from_action(item) for item in chief_brief.next_drill_readiness.must_do_before_drill[:3]]
    if not must_do:
        must_do = [_entry_from_action(item) for item in chief_brief.top_priority_items[:3]]
    should_do = [_entry_from_action(item) for item in actions if item.priority == "medium"][:5]
    can_defer = [_entry_from_action(item) for item in actions if item.priority == "low"][:5]
    blocked_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status == ActionStatus.blocked
    ][:2]
    active_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status in {ActionStatus.open, ActionStatus.in_progress}
    ][:4]
    waiting_entries = [
        _entry_from_tracked_action(item)
        for item in tracked_actions
        if item.status == ActionStatus.waiting
    ][:3]
    must_do = [*must_do, *blocked_entries][:6]
    should_do = [
        *active_entries,
        *should_do,
    ][:6]
    can_defer = [
        *waiting_entries,
        *can_defer,
    ][:6]

    waiting_on: list[str] = []
    if documentation_updates:
        waiting_on.append(
            f"{len(documentation_updates)} documentation update candidate(s) still need review or disposition."
        )
    if career_watch.tracked_opportunities:
        waiting_on.append(
            f"{len(career_watch.tracked_opportunities)} tracked opportunity record(s) need pursue/archive decisions."
        )
    if chief_brief.handoff_is_stale:
        waiting_on.append("Session handoff is stale and should be refreshed before relying on watch items.")
    waiting_on.extend(
        [
            f"{item.title} is waiting on {item.owner or 'an owner'}."
            for item in tracked_actions
            if item.status == ActionStatus.waiting
        ][:3]
    )

    blockers: list[str] = []
    blockers.extend(chief_brief.next_drill_readiness.missing_foundation[:3])
    if document_summary is not None:
        if document_summary.missing_recommended_types:
            blockers.append(
                "Missing recommended local documents: "
                + ", ".join(document_summary.missing_recommended_types[:4])
            )
        if document_summary.expired_count:
            blockers.append(f"{document_summary.expired_count} local document(s) are expired.")
    if any(item.category == "fitrep" for item in admin_readiness.items):
        blockers.append("FitRep watch items exist and still require confirmed support, routing, or suspense checks.")
    blockers.extend(
        [
            f"{item.title} is blocked{f' by {item.owner}' if item.owner else ''}."
            for item in tracked_actions
            if item.status == ActionStatus.blocked
        ][:3]
    )

    leverage_actions = [
        item.title for item in chief_brief.next_drill_readiness.must_do_before_drill[:3]
    ] or [
        item.title for item in chief_brief.top_priority_items[:3]
    ] or [
        "Refresh the session handoff.",
        "Confirm the next drill or admin suspense.",
        "Review source-update or opportunity watch items.",
    ]

    prep_follow_ups = [task.title for plan in chief_brief.drill_plans for task in plan.tasks[:2]][:4]
    if not prep_follow_ups:
        prep_follow_ups = chief_brief.next_drill_readiness.recommended_follow_on_workflows[:3] or [
            "Review the next drill-prep plan.",
            "Confirm travel, uniform, and gear timelines.",
        ]
    prep_follow_ups.extend(
        [
            f"{item.title} -> {item.owner or 'assign owner'}"
            for item in tracked_actions
            if item.status in {ActionStatus.open, ActionStatus.in_progress}
        ][:3]
    )

    return DailyOpsBrief(
        executive_snapshot=chief_brief.summary_lines[:3],
        must_do=must_do,
        should_do=should_do,
        can_defer=can_defer,
        waiting_on=waiting_on,
        blockers=blockers,
        leverage_actions=leverage_actions,
        prep_follow_ups=prep_follow_ups,
    )


def _analyst_brief(
    *,
    chief_brief: ChiefBriefResponse,
    admin_readiness: AdminReadinessResponse,
    career_watch: CareerWatchResponse,
    documentation_updates: list[DocumentationUpdateCandidate],
    tracked_actions: list[ActionRecord],
    tracked_opportunities: list[OpportunityRecord],
    document_summary: PersonalDocumentSummary | None,
) -> AnalystBrief:
    data_quality_notes: list[str] = []
    if document_summary is not None:
        data_quality_notes.extend(
            [
                f"{document_summary.total_documents} local document(s) indexed.",
                f"{document_summary.review_due_count} document(s) due for review.",
                f"{document_summary.expired_count} document(s) expired.",
            ]
        )
        if document_summary.pii_flagged_count:
            data_quality_notes.append(
                f"{document_summary.pii_flagged_count} local document(s) contain detected PII and need care."
            )
    if chief_brief.handoff_is_stale:
        data_quality_notes.append(
            "Session handoff is stale, which lowers confidence in career and admin watch signals."
        )

    kpi_summary = [
        f"{len(chief_brief.action_items)} total action item(s) in the Chief/Aide brief.",
        f"{len(admin_readiness.items)} admin readiness cue(s) currently surfaced.",
        f"{len(career_watch.watch_items)} career watch cue(s) currently surfaced.",
        f"{len(tracked_actions)} tracked POAM/action item(s) currently open.",
        f"{len(tracked_opportunities)} tracked opportunity record(s) in local storage.",
    ]

    anomalies: list[str] = []
    if documentation_updates:
        anomalies.append(
            f"{len(documentation_updates)} source update candidate(s) may indicate stale doctrine or admin references."
        )
    if document_summary is not None and document_summary.missing_recommended_types:
        anomalies.append("Core local support documents are incomplete for the current profile.")
    if chief_brief.handoff is None:
        anomalies.append("No session handoff is present, which makes the dashboard less personalized.")
    blocked_actions = [item for item in tracked_actions if item.status == ActionStatus.blocked]
    if blocked_actions:
        anomalies.append(f"{len(blocked_actions)} tracked action item(s) are blocked.")

    likely_causes = [
        "Reserve workflows are fragmented across local notes, watch items, and manually tracked opportunities.",
        "Action ownership and suspense discipline are still partly local and manually maintained.",
        "Source freshness depends on scans and human review rather than automatic authoritative reconciliation.",
    ]
    if documentation_updates:
        likely_causes.append(
            "Recent MARADMIN or MCPEL change signals have not yet been reviewed into the local corpus."
        )

    assumptions = [
        "Local uploads are advisory context only and are not authoritative doctrine or official records.",
        "Tracked opportunities do not establish eligibility, approval, or final availability.",
        "Unreviewed source updates should be treated as warnings, not confirmed changes.",
    ]

    follow_up_checks = [
        "Run or review document/source freshness checks before relying on older policy summaries.",
        "Refresh the handoff when PME, FitRep, or billet interests change.",
        "Confirm document gaps and expirations against real user-owned records.",
    ]
    if tracked_opportunities:
        follow_up_checks.append("Compare tracked opportunities against MOS, rank, geography, and timing before acting.")
    if tracked_actions:
        follow_up_checks.append("Review blocked and waiting action items for owner, suspense, and next-move clarity.")

    return AnalystBrief(
        executive_summary=chief_brief.summary_lines[:2] or ["Dashboard loaded with current local advisory context."],
        data_quality_notes=data_quality_notes,
        kpi_summary=kpi_summary,
        anomalies=anomalies,
        likely_causes=likely_causes,
        assumptions=assumptions,
        follow_up_checks=follow_up_checks,
    )


def _entry_from_action(item: ChiefActionItem) -> DailyOpsEntry:
    return DailyOpsEntry(
        title=item.title,
        detail=item.recommendation,
        category=item.category,
        priority=item.priority,
        due_date=item.due_date.isoformat() if item.due_date else None,
    )


def _entry_from_tracked_action(item: ActionRecord) -> DailyOpsEntry:
    detail_parts = [
        item.description or "",
        f"Owner: {item.owner}" if item.owner else "",
        f"Status: {item.status.value}",
        f"Suspense: {item.suspense_date.isoformat()}" if item.suspense_date else "",
    ]
    return DailyOpsEntry(
        title=item.title,
        detail=" | ".join(part for part in detail_parts if part),
        category=item.category.value,
        priority=item.priority.value,
        due_date=item.suspense_date.isoformat() if item.suspense_date else None,
    )
