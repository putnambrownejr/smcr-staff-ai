"""Baseline demo files for the dashboard's demo mode.

Toggling demo mode on in the dashboard re-seeds a shared demo user key
(`DEMO_USER_KEY`) with real entries -- markdown files under `User Docs/` and
tracked-action records -- so every workspace flow (FitRep sliders, notebook
saves, drafted-product open-location, action round-trips) works against
disposable content instead of the operator's personal data. Re-seeding wipes
and recreates the set, so each toggle gives a clean, known baseline for
testing and demos.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.schemas.actions import (
    ActionCategory,
    ActionItemRequest,
    ActionPriority,
    ActionStatus,
)
from app.schemas.chief_setup import ChiefSetupUpsertRequest
from app.schemas.user_docs import UserDocCategory, UserDocCreateRequest, UserDocUpdateRequest
from app.services.actions.tracker import ActionTracker
from app.services.chief.setup_store import ChiefSetupStore
from app.services.demo.scenarios import DEMO_USER_KEY
from app.services.user_docs.store import UserDocsStore


def demo_workspace_is_empty(store: UserDocsStore, tracker: ActionTracker) -> bool:
    """True when the demo user has no baseline docs or actions yet."""
    for category in UserDocCategory:
        if store.list_category(category, DEMO_USER_KEY):
            return False
    return not any(r.user_key == DEMO_USER_KEY for r in tracker.list(user_key=DEMO_USER_KEY, include_closed=True))


def seed_demo_workspace(
    store: UserDocsStore,
    tracker: ActionTracker,
    chief_store: ChiefSetupStore | None = None,
    *,
    only_if_empty: bool = False,
) -> dict[str, int] | None:
    """Wipe and recreate the demo user's baseline files. Returns counts.

    With ``only_if_empty=True``, does nothing and returns ``None`` when the
    demo workspace already has content -- so a page reload mid-demo keeps the
    operator's demo-session edits, while an explicit toggle (the default) always
    resets to a known baseline.
    """
    if only_if_empty and not demo_workspace_is_empty(store, tracker):
        return None
    _wipe_demo_docs(store)
    _wipe_demo_actions(tracker)
    counts = {
        "notebook": _seed_notebook(store),
        "fitreps": _seed_fitreps(store),
        "generations": _seed_generations(store),
        "actions": _seed_actions(tracker),
    }
    if chief_store is not None:
        counts["chief_setup"] = _seed_chief_setup(chief_store)
    return counts


def _seed_chief_setup(chief_store: ChiefSetupStore) -> int:
    chief_store.upsert(
        DEMO_USER_KEY,
        ChiefSetupUpsertRequest(
            unit="4th CAG",
            billet="S-4A / Logistics",
            echelon="Battalion",
            drill_schedule="09-10 AUG (next drill)",
            commander_intent="Rebuild the reserve bench: readiness, retention, and a clean AT.",
            priorities=[
                "Close the three open RQS entries before drill",
                "FitReps for Sgt Alvarez and Cpl Diaz by 31 AUG",
                "Confirm AT travel claims are submitted in DTS",
            ],
            battle_rhythm=[
                "0730 COC sync each drill morning",
                "1600 debrief to the SgtMaj",
                "Post-drill handoff before close of business Sunday",
            ],
            watch_items=[
                "FY27 Reserve Component AT budget MARADMIN",
                "Update to FitRep reporting occasions for SMCR",
            ],
            output_format="Bullet",
            tone="Direct and brief",
            standing_notes="Keep me ahead of suspenses. Flag anything that needs a commander's decision early.",
        ),
    )
    return 1


def _wipe_demo_docs(store: UserDocsStore) -> None:
    for category in UserDocCategory:
        for entry in store.list_category(category, DEMO_USER_KEY):
            store.delete(category, DEMO_USER_KEY, entry.id)


def _wipe_demo_actions(tracker: ActionTracker) -> None:
    # list(user_key=...) also matches records with no user_key at all; only
    # delete records that are explicitly the demo user's.
    for record in tracker.list(user_key=DEMO_USER_KEY, include_closed=True):
        if record.user_key == DEMO_USER_KEY:
            tracker.delete(record.action_id)


def _seed_notebook(store: UserDocsStore) -> int:
    notes = [
        UserDocCreateRequest(
            title="Armory opening checklist",
            body=(
                "1. Sign for keys at the duty desk (log book, not the clipboard).\n"
                "2. Combo is on the S-4 safe card — demo placeholder, not a real combo.\n"
                "3. Lights, then dehumidifier readings into the green binder.\n"
                "4. Count racks 1–14 before opening the issue window.\n"
            ),
        ),
        UserDocCreateRequest(
            title="New join checklist — S-1 lane",
            body=(
                "- MOL check-in same day; RUC/MCC transfer confirmed by S-1 chief.\n"
                "- DTS profile + GTCC status before the first AT window.\n"
                "- RQS entry and MCTFS audit within the first drill weekend.\n"
            ),
        ),
        UserDocCreateRequest(
            title="Old drill rhythm notes",
            body=(
                "Kept for reference — superseded by the battle rhythm board.\n"
                "0730 COC sync / 0800 formation / 1600 debrief to the SgtMaj.\n"
            ),
            fields={"archived": True},
        ),
    ]
    for request in notes:
        store.create(UserDocCategory.notebook, DEMO_USER_KEY, request)
    return len(notes)


def _seed_fitreps(store: UserDocsStore) -> int:
    reports = [
        UserDocCreateRequest(
            title="Alvarez, R.",
            fields={
                "archived": False,
                "rank": "Sgt",
                "unit": "H&S Co, 4th CAG",
                "period": "AUG25–JUL26",
                "role": "RS",
                "scores": {"mission": 5, "individual": 4, "leadership": 5, "intellect": 3, "fitness": 4},
                "statement": (
                    "Demo baseline report. Sgt Alvarez led the RQS reconciliation effort "
                    "across two drill weekends and briefed the results to the company "
                    "first sergeant without prompting."
                ),
                "notes": "Watch for profile inflation — second report this cycle.",
                "tree": 0,
                "roComments": "",
            },
        ),
        UserDocCreateRequest(
            title="Diaz, M.",
            fields={
                "archived": False,
                "rank": "Cpl",
                "unit": "Supply Co, 4th CAG",
                "period": "FEB26–JUL26",
                "role": "RS",
                "scores": {"mission": 4, "individual": 4, "leadership": 5, "intellect": 4, "fitness": 4},
                "statement": (
                    "Demo baseline report. Cpl Diaz ran the supply cage solo during the "
                    "AT period and closed out all open CMRs before endex."
                ),
                "notes": "PME gap flagged — Corporals Course seat requested.",
                "tree": 0,
                "roComments": "",
            },
        ),
    ]
    for request in reports:
        store.create(UserDocCategory.fitreps, DEMO_USER_KEY, request)
    return len(reports)


def _seed_generations(store: UserDocsStore) -> int:
    drafts = [
        (
            "SITREP",
            "sitrep",
            "Staff product",
            {
                "lineOne": "4th CAG COC, 121800Z JUL 26",
                "situation": "Drill weekend day one complete; all planned events executed on timeline.",
                "significantActivity": "RQS reconciliation closed 11 of 14 open entries; remainder await MROWS.",
                "personnelStatus": "92% present; two Marines on approved absence, one medical waiver pending.",
                "logisticsStatus": "Chow and transport confirmed for day two; one 7-ton deadlined for brakes.",
                "recommendations": "Request S-4 confirm backup transport before 0600 formation.",
            },
        ),
        (
            "AAR",
            "aar",
            "Staff product",
            {
                "eventDescription": "Battalion command post exercise, planning-process focus.",
                "sustains": "COA development was disciplined; red cell challenge produced real branch plans.",
                "improves": "Sync matrix ownership was unclear; two staff sections briefed from stale copies.",
                "actionItems": "S-3 owns a single sync matrix source by next drill; ops chief to confirm.",
            },
        ),
    ]
    for title, template_type, kind, data in drafts:
        entry = store.create(
            UserDocCategory.generations,
            DEMO_USER_KEY,
            UserDocCreateRequest(title=title, fields={"templateType": template_type, "kind": kind}),
        )
        # The dashboard reveals drafts at "User Docs/Generations/<id>.md", so
        # the persisted path must carry the real id (mirrors what the bundle
        # writes after a live create).
        store.update(
            UserDocCategory.generations,
            DEMO_USER_KEY,
            entry.id,
            UserDocUpdateRequest(
                fields={
                    "templateType": template_type,
                    "kind": kind,
                    "path": f"User Docs/Generations/{entry.id}.md",
                    "receiptsFolder": f"User Docs/Generations/{entry.id}-receipts/",
                    "receipts": [],
                    "data": data,
                }
            ),
        )
    return len(drafts)


def _seed_actions(tracker: ActionTracker) -> int:
    today = date.today()
    actions = [
        ActionItemRequest(
            user_key=DEMO_USER_KEY,
            title="Submit AT travel claim in DTS",
            owner="You",
            category=ActionCategory.travel,
            priority=ActionPriority.high,
            status=ActionStatus.open,
            suspense_date=today + timedelta(days=5),
            notes="Receipts are in the drafted DTS checklist.",
        ),
        ActionItemRequest(
            user_key=DEMO_USER_KEY,
            title="FitRep input for Sgt Alvarez",
            owner="You",
            category=ActionCategory.fitrep,
            priority=ActionPriority.medium,
            status=ActionStatus.waiting,
            suspense_date=today + timedelta(days=20),
            notes="Waiting on RO comments before routing.",
        ),
        ActionItemRequest(
            user_key=DEMO_USER_KEY,
            title="Reconcile RQS roster against MROWS",
            owner="S-1 chief",
            category=ActionCategory.admin,
            priority=ActionPriority.medium,
            status=ActionStatus.blocked,
            notes="Blocked by pending MROWS access request.",
        ),
    ]
    tracker.track(actions)
    return len(actions)
