from datetime import date
from pathlib import Path

from app.api.routes import dashboard
from app.schemas.actions import ActionItemRequest
from app.schemas.battle_rhythm import BattleRhythmBoardUpsertRequest, BattleRhythmEntryInput
from app.schemas.calendar import DrillPrepPlanResponse, PrepTask
from app.schemas.opportunities import ManualOpportunityRequest
from app.schemas.section_memory import SectionMemoryEntry, SectionMemoryProfileUpsertRequest
from app.schemas.session import UserSessionHandoff
from app.schemas.source_state import VerifiedSourceState
from app.schemas.source_updates import DocumentationUpdateCandidate, UpdateTriggerType
from app.services.actions.tracker import ActionTracker
from app.services.calendar.plan_store import DrillPrepPlanStore
from app.services.connectors.travel_case_store import TravelCaseStore
from app.services.ingestion.document_update_store import DocumentUpdateStore
from app.services.ingestion.source_state_store import SourceStateStore
from app.services.opportunities.tracker import OpportunityTracker
from app.services.reading.catalog import ReadingListCatalogService
from app.services.session.handoff_store import SessionHandoffStore
from app.services.staff.battle_rhythm_store import BattleRhythmStore
from app.services.staff.section_memory_store import SectionMemoryStore


def test_runtime_stores_use_injected_temp_paths_without_localappdata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    local_app_data = tmp_path / "localappdata"
    storage_root = tmp_path / "runtime"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    action_store = ActionTracker(storage_root / "actions")
    action = action_store.track([ActionItemRequest(title="Confirm roster", category="admin")])[0]
    assert action_store.get(action.action_id) is not None

    update_store = DocumentUpdateStore(storage_root / "updates")
    update_store.save_many(
        [
            DocumentationUpdateCandidate(
                candidate_id="candidate-1",
                tracked_title="PES",
                trigger_type=UpdateTriggerType.manual_review,
            )
        ]
    )
    assert update_store.get("candidate-1") is not None

    plan_store = DrillPrepPlanStore(storage_root / "plans")
    plan_store.save(
        DrillPrepPlanResponse(
            id="plan-1",
            drill_date=date(2026, 6, 6),
            tasks=[PrepTask(title="Pack gear", due_offset_days=3, due_date=date(2026, 6, 3), category="gear")],
        )
    )
    assert plan_store.get("plan-1") is not None

    opportunity_store = OpportunityTracker(storage_root / "opportunities")
    opportunity_store.track([ManualOpportunityRequest(title="ADOS Planner")])
    assert opportunity_store.list()

    source_state_store = SourceStateStore(storage_root / "source_states")
    source_state_store.save(VerifiedSourceState(source_state_id="source-1", tracked_title="MCRAMM"))
    assert source_state_store.get("source-1") is not None

    handoff_store = SessionHandoffStore(storage_root / "handoffs")
    handoff_store.upsert(UserSessionHandoff(user_key="capt-temp"))
    assert handoff_store.get("capt-temp") is not None

    battle_rhythm_store = BattleRhythmStore(storage_root / "battle_rhythm")
    battle_rhythm_store.upsert(
        "capt-temp",
        BattleRhythmBoardUpsertRequest(
            board_title="Temp board",
            assumption_log=[BattleRhythmEntryInput(text="Support remains available.")],
        ),
    )
    assert battle_rhythm_store.get("capt-temp") is not None

    section_memory_store = SectionMemoryStore(storage_root / "section_memory")
    section_memory_store.upsert(
        "capt-temp",
        SectionMemoryProfileUpsertRequest(
            entries=[SectionMemoryEntry(section="S-3", title="Training", notes=["Keep objectives measurable."])]
        ),
    )
    assert section_memory_store.get("capt-temp") is not None

    TravelCaseStore(storage_root / "travel_cases")

    assert not local_app_data.exists()


def test_dashboard_seed_and_sources_load_when_cwd_is_not_repo_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    dashboard._reference_library_cache = None

    catalog = ReadingListCatalogService.from_yaml(dashboard.SEED_DIR / "reading_list.example.yaml")
    references = dashboard._reference_library()

    assert catalog.list_books()
    assert references
