# Family and Deployment Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add saved, event-based family/deployment readiness checklists to Bench+Files with safe calendar export, spouse-friendly summaries, and a dedicated readiness advisor.

**Architecture:** Introduce one typed JSON domain under the local state root, following the FitRep/Travel store patterns. A small builder owns duration bands, baseline checklist composition, and milestone generation; routes expose CRUD, item updates, ICS export, and summary creation. The compiled dashboard remains generated through `scripts/patch_dashboard_bundle.py`.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, flat JSON storage, vanilla JS compiled dashboard, pytest, Playwright, mypy, ruff.

## Global Constraints

- UNCLASSIFIED information only.
- Do not store mission details, precise unit movements, SSNs, dependent identity records, medical records, account credentials, legal-document contents, or unnecessary PII.
- Family readiness remains a Bench+Files workflow; do not add a workspace or top-level lane.
- Legal and DEERS features are completion tracking plus official link-outs, not legal-document generation or systems integration.
- Every generated checklist, summary, or advisory includes `DRAFT — Verify all references against current official sources before acting.`
- No new runtime dependency, database migration, cloud service, frontend framework, background scheduler, or authentication integration.
- Demo records must be explicitly tagged and disappear immediately when Demo mode is off.

---

## File Structure

- Create `app/schemas/family_readiness.py`: typed event, item, contact, glossary, milestone, and request/response models.
- Create `app/services/family_readiness/__init__.py`: package marker.
- Create `app/services/family_readiness/builder.py`: duration bands, baseline items, milestone generation, summary rendering.
- Create `app/services/family_readiness/store.py`: user-key-scoped JSON persistence and item updates.
- Create `app/services/family_readiness/calendar.py`: safe generic ICS rendering.
- Create `app/api/routes/family_readiness.py`: CRUD, item status, summary, and ICS endpoints.
- Modify `app/core/config.py`: configured family-readiness storage directory.
- Modify `app/main.py`: register the route.
- Modify `app/services/agents/source_refs.py`: official family/deployment source pack.
- Modify `app/services/agents/readiness_development_agents.py`: advisor builder.
- Modify `app/services/agents/registry.py`: registry/category integration.
- Modify `scripts/patch_dashboard_bundle.py`: Bench+Files tile, saved-event editor, summary and ICS actions.
- Regenerate `app/static/dashboard/index.html`: compiled dashboard output only.
- Create `tests/test_family_readiness_builder.py`, `tests/test_family_readiness_store.py`, and `tests/test_family_readiness_routes.py`.
- Modify `tests/test_agent_registry.py`, `tests/test_dashboard.py`, and `tests/e2e/test_dashboard_flows.py`.

### Task 1: Typed checklist composition

**Files:**
- Create: `app/schemas/family_readiness.py`
- Create: `app/services/family_readiness/__init__.py`
- Create: `app/services/family_readiness/builder.py`
- Test: `tests/test_family_readiness_builder.py`

**Interfaces:**
- Produces: `ReadinessDurationBand`, `FamilyReadinessEventCreateRequest`, `FamilyReadinessEvent`, `build_event(request)`, `render_spouse_summary(event)`.
- Consumes: Python `date`, Pydantic models, no store or HTTP layer.

- [ ] **Step 1: Write failing duration, baseline, milestone, and redaction tests**

```python
from datetime import date

from app.schemas.family_readiness import FamilyReadinessEventCreateRequest, ReadinessDurationBand
from app.services.family_readiness.builder import build_event, render_spouse_summary


def test_extended_at_builds_short_duration_baseline() -> None:
    event = build_event(FamilyReadinessEventCreateRequest(
        user_key="capt-family",
        title="Extended AT 2027",
        approximate_start=date(2027, 7, 1),
        approximate_end=date(2027, 7, 28),
    ))
    assert event.duration_band is ReadinessDurationBand.short
    assert {item.category.value for item in event.items} >= {"legal", "deers", "contacts", "opsec"}
    assert any(item.source_url and "tricare.mil/DEERS" in item.source_url for item in event.items)
    assert any(milestone.label.startswith("T-") for milestone in event.milestones)


def test_long_absence_adds_reintegration_and_summary_redacts_private_data() -> None:
    event = build_event(FamilyReadinessEventCreateRequest(
        user_key="capt-family",
        title="Overseas orders 2028",
        approximate_start=date(2028, 1, 1),
        approximate_end=date(2028, 12, 1),
    ))
    assert event.duration_band is ReadinessDurationBand.long
    assert any(item.category.value == "reintegration" for item in event.items)
    event.private_notes = "Do not share this note."
    summary = render_spouse_summary(event)
    assert "Do not share this note" not in summary
    assert "DRAFT — Verify all references" in summary
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `uv run pytest tests/test_family_readiness_builder.py -q`

Expected: collection fails because `app.schemas.family_readiness` does not exist.

- [ ] **Step 3: Add the typed models**

```python
class ReadinessDurationBand(StrEnum):
    short = "short"
    medium = "medium"
    long = "long"
    custom = "custom"


class ReadinessEventStatus(StrEnum):
    planning = "planning"
    active = "active"
    reintegration = "reintegration"
    archived = "archived"


class ReadinessItemStatus(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    complete = "complete"
    not_applicable = "not_applicable"


class ReadinessItemCategory(StrEnum):
    administration = "administration"
    legal = "legal"
    deers = "deers"
    household = "household"
    contacts = "contacts"
    opsec = "opsec"
    family_support = "family_support"
    reintegration = "reintegration"


class FamilyReadinessChecklistItem(BaseModel):
    item_id: str
    category: ReadinessItemCategory
    task: str
    plain_language: str
    status: ReadinessItemStatus = ReadinessItemStatus.not_started
    responsible_label: str = ""
    target_date: date | None = None
    notes: str = ""
    source_url: str | None = None
    origin: Literal["baseline", "duration", "user"] = "baseline"
    shareable: bool = True


class FamilyReadinessMilestone(BaseModel):
    milestone_id: str
    label: str
    title: str
    target_date: date


class FamilyReadinessContact(BaseModel):
    contact_id: str
    role: str
    organization: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    source_url: str | None = None
    last_verified_at: datetime | None = None
    shareable: bool = True


class FamilyReadinessGlossaryEntry(BaseModel):
    term: str
    expansion: str
    plain_language: str
    shareable: bool = True


class FamilyReadinessEventCreateRequest(BaseModel):
    user_key: str
    title: str = Field(min_length=1, max_length=200)
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand | None = None


class FamilyReadinessEvent(BaseModel):
    event_id: str
    user_key: str
    title: str
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand
    status: ReadinessEventStatus = ReadinessEventStatus.planning
    items: list[FamilyReadinessChecklistItem] = Field(default_factory=list)
    contacts: list[FamilyReadinessContact] = Field(default_factory=list)
    glossary: list[FamilyReadinessGlossaryEntry] = Field(default_factory=list)
    milestones: list[FamilyReadinessMilestone] = Field(default_factory=list)
    private_notes: str = ""
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime


class FamilyReadinessEventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    approximate_start: date | None = None
    approximate_end: date | None = None
    duration_band: ReadinessDurationBand | None = None
    status: ReadinessEventStatus | None = None
    private_notes: str | None = None


class FamilyReadinessItemUpdateRequest(BaseModel):
    status: ReadinessItemStatus | None = None
    responsible_label: str | None = None
    target_date: date | None = None
    notes: str | None = None
    shareable: bool | None = None


class FamilyReadinessItemCreateRequest(BaseModel):
    category: ReadinessItemCategory
    task: str = Field(min_length=1, max_length=240)
    plain_language: str = Field(min_length=1, max_length=500)
    responsible_label: str = ""
    target_date: date | None = None
    notes: str = ""
    shareable: bool = True


class FamilyReadinessItemOrderRequest(BaseModel):
    item_ids: list[str] = Field(min_length=1)


class FamilyReadinessContactUpsertRequest(BaseModel):
    contact_id: str | None = None
    role: str = Field(min_length=1, max_length=120)
    organization: str = ""
    phone: str = ""
    email: str = ""
    notes: str = ""
    source_url: str | None = None
    shareable: bool = True


class FamilyReadinessGlossaryUpsertRequest(BaseModel):
    term: str = Field(min_length=1, max_length=80)
    expansion: str = Field(min_length=1, max_length=160)
    plain_language: str = Field(min_length=1, max_length=500)
    shareable: bool = True


class FamilyReadinessMilestoneUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    target_date: date | None = None


class FamilyReadinessEventListResponse(BaseModel):
    total_events: int
    records: list[FamilyReadinessEvent] = Field(default_factory=list)
```

- [ ] **Step 4: Implement deterministic composition and safe summary rendering**

```python
DRAFT_FOOTER = "DRAFT — Verify all references against current official sources before acting."
DEERS_URL = "https://www.tricare.mil/DEERS"
RAPIDS_URL = "https://idco.dmdc.osd.mil/idco/"
DEPLOYMENT_URL = "https://planmydeployment.militaryonesource.mil/pre-deployment"

BASELINE_ITEM_DEFINITIONS = [
    ("administration", "Confirm the unit-provided readiness checklist",
     "Ask which unit requirements and deadlines apply to this absence.", None),
    ("contacts", "Record the unit readiness or family-support contact",
     "Keep the role and public or user-approved contact method available to the household.", None),
    ("legal", "Schedule an installation legal-assistance review",
     "A qualified legal-assistance provider should review legal readiness; this app does not draft legal documents.",
     DEPLOYMENT_URL),
    ("legal", "Review whether a limited or special power of attorney is needed",
     "Ask legal assistance and any affected institution what form and scope they require.", DEPLOYMENT_URL),
    ("legal", "Review wills, emergency data, beneficiaries, and document access",
     "Confirm current records and how the trusted support person can reach the right office without storing contents here.",
     DEPLOYMENT_URL),
    ("deers", "Review DEERS contact information",
     "Confirm address, email, and phone information through the official DEERS channels.", DEERS_URL),
    ("deers", "Check dependent ID-card expiration dates",
     "Use the RAPIDS locator for an appointment if an eligible family member needs an ID-card action.", RAPIDS_URL),
    ("household", "Review recurring household responsibilities",
     "Agree who will handle bills, vehicles, housing, pets, mail, and urgent repairs without recording account credentials.", None),
    ("contacts", "Validate emergency contacts and backup support",
     "Make sure the household knows who to call if the primary contact is unavailable.", None),
    ("opsec", "Agree on a communication rhythm and backup method",
     "Set expectations for normal delays and a safe backup method without sharing mission or movement details.", DEPLOYMENT_URL),
    ("opsec", "Review family OPSEC reminders",
     "Do not publish exact dates, routes, locations, missions, or information showing that a household is unattended.",
     DEPLOYMENT_URL),
    ("family_support", "Review child, pet, school, employer, caregiver, or special-support coordination",
     "Mark only the relevant planning categories and keep names, diagnoses, and custody details outside this checklist.",
     DEPLOYMENT_URL),
]


def select_duration_band(start: date | None, end: date | None) -> ReadinessDurationBand:
    if start is None or end is None or end < start:
        return ReadinessDurationBand.custom
    days = (end - start).days + 1
    if 14 <= days <= 30:
        return ReadinessDurationBand.short
    if days <= 180:
        return ReadinessDurationBand.medium
    if days <= 395:
        return ReadinessDurationBand.long
    return ReadinessDurationBand.custom


def build_event(request: FamilyReadinessEventCreateRequest) -> FamilyReadinessEvent:
    now = datetime.now(UTC)
    band = request.duration_band or select_duration_band(request.approximate_start, request.approximate_end)
    return FamilyReadinessEvent(
        event_id=secrets.token_hex(10), user_key=request.user_key, title=request.title.strip(),
        approximate_start=request.approximate_start, approximate_end=request.approximate_end,
        duration_band=band, items=_baseline_items(band),
        milestones=_milestones(request.approximate_start, request.approximate_end),
        glossary=_baseline_glossary(), created_at=now, updated_at=now,
    )


def _milestones(start: date | None, end: date | None) -> list[FamilyReadinessMilestone]:
    if start is None:
        return []
    definitions = [(90, "T-90", "Start legal and household readiness review"),
                   (60, "T-60", "Review DEERS contact information"),
                   (30, "T-30", "Validate contacts and household continuity"),
                   (14, "T-14", "Review communication rhythm and OPSEC"),
                   (7, "T-7", "Complete final personal-readiness check")]
    milestones = [FamilyReadinessMilestone(milestone_id=secrets.token_hex(8), label=label,
                                           title=title, target_date=start - timedelta(days=offset))
                  for offset, label, title in definitions]
    if end is not None:
        milestones.append(FamilyReadinessMilestone(milestone_id=secrets.token_hex(8), label="Return window",
                                                    title="Begin household reintegration review", target_date=end))
    return milestones


def _baseline_glossary() -> list[FamilyReadinessGlossaryEntry]:
    definitions = [
        ("AT", "Annual Training", "A scheduled period of active-duty training for a reserve member."),
        ("DEERS", "Defense Enrollment Eligibility Reporting System",
         "The Defense Department eligibility record used for benefits such as TRICARE."),
        ("RAPIDS", "Real-Time Automated Personnel Identification System",
         "The ID-card office system and locator used for military identification-card services."),
        ("POA", "Power of Attorney",
         "A legal document prepared or reviewed with qualified legal assistance that authorizes another person to act in defined matters."),
        ("OPSEC", "Operations Security",
         "Practices that protect sensitive details such as exact dates, locations, routes, and mission information."),
        ("milConnect", "milConnect",
         "An official online service for selected personnel, benefits, and DEERS-related actions."),
    ]
    return [FamilyReadinessGlossaryEntry(term=term, expansion=expansion, plain_language=plain)
            for term, expansion, plain in definitions]


def render_spouse_summary(event: FamilyReadinessEvent) -> str:
    tasks = [f"- [{ 'x' if item.status.value == 'complete' else ' ' }] {item.task}" for item in event.items if item.shareable]
    contacts = [f"- {item.role}: {item.organization} {item.phone} {item.email}".rstrip() for item in event.contacts if item.shareable]
    terms = [f"- **{item.term} — {item.expansion}:** {item.plain_language}" for item in event.glossary if item.shareable]
    return "\n".join([f"# {event.title}", "", "## Readiness checklist", *tasks, "", "## Contacts", *contacts,
                      "", "## Plain-language guide", *terms, "", DRAFT_FOOTER])
```

Populate `_baseline_items`, `_milestones`, and `_baseline_glossary` with the exact categories and official URLs in the approved design. Milestones must contain generic personal-readiness actions only.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/test_family_readiness_builder.py -q`

Expected: all tests pass.

```powershell
git add app/schemas/family_readiness.py app/services/family_readiness tests/test_family_readiness_builder.py
git commit -m "feat: model family readiness events"
```

### Task 2: Local persistence and CRUD routes

**Files:**
- Create: `app/services/family_readiness/store.py`
- Create: `app/api/routes/family_readiness.py`
- Modify: `app/core/config.py`
- Modify: `app/main.py`
- Test: `tests/test_family_readiness_store.py`
- Test: `tests/test_family_readiness_routes.py`

**Interfaces:**
- Consumes: `build_event`, schemas from Task 1, `is_valid_user_key`.
- Produces: `FamilyReadinessStore` and `/family-readiness/{user_key}` routes.

- [ ] **Step 1: Write failing store and route tests**

```python
def test_store_creates_updates_and_archives_user_scoped_event(tmp_path: Path) -> None:
    store = FamilyReadinessStore(tmp_path / "family-readiness")
    event = store.create(FamilyReadinessEventCreateRequest(user_key="capt-family", title="Extended AT"))
    updated = store.update_item("capt-family", event.event_id, event.items[0].item_id,
                                FamilyReadinessItemUpdateRequest(status="complete"))
    assert updated.items[0].status.value == "complete"
    assert store.list("different-user") == []
    archived = store.update_event("capt-family", event.event_id,
                                  FamilyReadinessEventUpdateRequest(status="archived"))
    assert archived.status.value == "archived"


def test_family_readiness_routes_reject_user_key_mismatch(tmp_path: Path) -> None:
    store = FamilyReadinessStore(tmp_path)
    app.dependency_overrides[get_family_readiness_store] = lambda: store
    client = TestClient(app)
    response = client.post("/family-readiness/capt-family", json={"user_key": "other-user", "title": "AT"})
    assert response.status_code == 400
```

- [ ] **Step 2: Run focused tests and verify RED**

Run: `uv run pytest tests/test_family_readiness_store.py tests/test_family_readiness_routes.py -q`

Expected: import failures for the missing store and route.

- [ ] **Step 3: Implement a user-digest file-per-event store**

```python
class FamilyReadinessStore:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list(self, user_key: str) -> list[FamilyReadinessEvent]:
        if not is_valid_user_key(user_key):
            return []
        prefix = f"{hashlib.sha256(user_key.encode()).hexdigest()[:24]}-"
        records = [FamilyReadinessEvent.model_validate_json(path.read_text(encoding="utf-8"))
                   for path in self.root_dir.glob(f"{prefix}*.json")]
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    def create(self, request: FamilyReadinessEventCreateRequest) -> FamilyReadinessEvent:
        if not is_valid_user_key(request.user_key):
            raise ValueError("Invalid user_key.")
        event = build_event(request)
        self._write(event)
        return event

    def update_item(self, user_key: str, event_id: str, item_id: str,
                    request: FamilyReadinessItemUpdateRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        found = False
        items = []
        for item in event.items:
            if item.item_id == item_id:
                found = True
                item = item.model_copy(update=request.model_dump(exclude_none=True))
            items.append(item)
        if not found:
            raise ValueError(f"Unknown readiness item: {item_id}")
        updated = event.model_copy(update={"items": items, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def add_item(self, user_key: str, event_id: str,
                 request: FamilyReadinessItemCreateRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        item = FamilyReadinessChecklistItem(item_id=secrets.token_hex(8), origin="user",
                                            **request.model_dump())
        updated = event.model_copy(update={"items": [*event.items, item], "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def reorder_items(self, user_key: str, event_id: str,
                      request: FamilyReadinessItemOrderRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        if set(request.item_ids) != {item.item_id for item in event.items}:
            raise ValueError("Item order must contain every checklist item exactly once.")
        by_id = {item.item_id: item for item in event.items}
        updated = event.model_copy(update={"items": [by_id[item_id] for item_id in request.item_ids],
                                           "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated
```

Add the remaining store methods exactly around the same `_require` boundary:

```python
    def get(self, user_key: str, event_id: str) -> FamilyReadinessEvent | None:
        if not is_valid_user_key(user_key):
            return None
        path = self._path(user_key, event_id)
        if not path.exists():
            return None
        return FamilyReadinessEvent.model_validate_json(path.read_text(encoding="utf-8"))

    def update_event(self, user_key: str, event_id: str,
                     request: FamilyReadinessEventUpdateRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        values = request.model_dump(exclude_none=True)
        updated = event.model_copy(update={**values, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def upsert_contact(self, user_key: str, event_id: str,
                       request: FamilyReadinessContactUpsertRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        contact_id = request.contact_id or secrets.token_hex(8)
        contact = FamilyReadinessContact(contact_id=contact_id,
                                         **request.model_dump(exclude={"contact_id"}))
        contacts = [contact if item.contact_id == contact_id else item for item in event.contacts]
        if not any(item.contact_id == contact_id for item in event.contacts):
            contacts.append(contact)
        updated = event.model_copy(update={"contacts": contacts, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def upsert_glossary(self, user_key: str, event_id: str,
                        request: FamilyReadinessGlossaryUpsertRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        entry = FamilyReadinessGlossaryEntry(**request.model_dump())
        entries = [entry if item.term.casefold() == entry.term.casefold() else item for item in event.glossary]
        if not any(item.term.casefold() == entry.term.casefold() for item in event.glossary):
            entries.append(entry)
        updated = event.model_copy(update={"glossary": entries, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def update_milestone(self, user_key: str, event_id: str, milestone_id: str,
                         request: FamilyReadinessMilestoneUpdateRequest) -> FamilyReadinessEvent:
        event = self._require(user_key, event_id)
        values = request.model_dump(exclude_none=True)
        found = any(item.milestone_id == milestone_id for item in event.milestones)
        if not found:
            raise ValueError(f"Unknown readiness milestone: {milestone_id}")
        milestones = [item.model_copy(update=values) if item.milestone_id == milestone_id else item
                      for item in event.milestones]
        updated = event.model_copy(update={"milestones": milestones, "updated_at": datetime.now(UTC)})
        self._write(updated)
        return updated

    def delete(self, user_key: str, event_id: str) -> bool:
        path = self._path(user_key, event_id)
        if not is_valid_user_key(user_key) or not path.exists():
            return False
        path.unlink()
        return True

    def _require(self, user_key: str, event_id: str) -> FamilyReadinessEvent:
        event = self.get(user_key, event_id)
        if event is None:
            raise ValueError(f"Unknown family readiness event: {event_id}")
        return event

    def _write(self, event: FamilyReadinessEvent) -> None:
        self._path(event.user_key, event.event_id).write_text(event.model_dump_json(indent=2), encoding="utf-8")

    def _path(self, user_key: str, event_id: str) -> Path:
        digest = hashlib.sha256(user_key.encode()).hexdigest()[:24]
        safe_id = "".join(char for char in event_id if char.isalnum() or char in {"-", "_"})
        return self.root_dir / f"{digest}-{safe_id}.json"
```

- [ ] **Step 4: Configure storage and register routes**

```python
def default_family_readiness_dir() -> Path:
    return default_local_context_dir() / "family_readiness"

# Settings
family_readiness_storage_dir: str = str(default_family_readiness_dir())
```

Add the configured directory to `configured_storage_dirs`. Import `family_readiness` in `app/main.py` and call `app.include_router(family_readiness.router)` near the other readiness routes.

Expose `GET/POST /family-readiness/{user_key}`, `GET/PATCH/DELETE /family-readiness/{user_key}/{event_id}`, `POST /items`, `PATCH /items/{item_id}`, `PUT /item-order`, `POST/DELETE /contacts`, `PUT/DELETE /glossary/{term}`, and `PATCH /milestones/{milestone_id}` beneath the event path. Every body containing `user_key` must match the path. Contact/glossary deletion rebuilds the list without the requested ID/term and returns 404 when nothing changed.

- [ ] **Step 5: Run focused tests and commit**

Run: `uv run pytest tests/test_family_readiness_store.py tests/test_family_readiness_routes.py -q`

Expected: all tests pass.

```powershell
git add app/core/config.py app/main.py app/api/routes/family_readiness.py app/services/family_readiness/store.py tests/test_family_readiness_store.py tests/test_family_readiness_routes.py
git commit -m "feat: persist family readiness checklists"
```

### Task 3: Safe ICS and spouse-summary outputs

**Files:**
- Create: `app/services/family_readiness/calendar.py`
- Modify: `app/api/routes/family_readiness.py`
- Modify: `tests/test_family_readiness_routes.py`

**Interfaces:**
- Consumes: `FamilyReadinessEvent`, `render_spouse_summary`, `UserDocsStore`.
- Produces: `FamilyReadinessIcsProvider.export(event) -> str`, summary generation entry.

- [ ] **Step 1: Add failing export and redaction tests**

```python
def test_event_ics_contains_only_generic_milestones(client: TestClient) -> None:
    response = client.get(f"/family-readiness/capt-family/{event_id}/ics")
    assert response.status_code == 200
    assert response.text.startswith("BEGIN:VCALENDAR")
    assert "Review DEERS contact information" in response.text
    assert "destination" not in response.text.lower()
    assert "mission" not in response.text.lower()


def test_summary_is_saved_as_generation_without_private_notes(client: TestClient) -> None:
    response = client.post(f"/family-readiness/capt-family/{event_id}/summary", json={"user_key": "capt-family"})
    assert response.status_code == 201
    assert response.json()["category"] == "generations"
    assert "private note" not in response.json()["body"]
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_family_readiness_routes.py -q`

Expected: 404 for the new `/ics` and `/summary` routes.

- [ ] **Step 3: Implement generic ICS rendering**

```python
class FamilyReadinessIcsProvider:
    def export(self, event: FamilyReadinessEvent) -> str:
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//smcr-staff-ai//family-readiness//EN"]
        for milestone in event.milestones:
            lines.extend(["BEGIN:VEVENT", f"UID:{event.event_id}-{milestone.milestone_id}@smcr-staff-ai",
                          f"DTSTART;VALUE=DATE:{milestone.target_date:%Y%m%d}",
                          f"SUMMARY:{_escape_ics(milestone.title)}",
                          "DESCRIPTION:DRAFT — Verify all references against current official sources before acting.",
                          "END:VEVENT"])
        return "\r\n".join([*lines, "END:VCALENDAR", ""])
```

Reuse the escaping behavior in `app/services/calendar/providers.py`; do not include location, mission, route, unit movement, or private notes.

- [ ] **Step 4: Add ICS and User Docs summary routes**

Use `Response(media_type="text/calendar")` for ICS. For summary, inject `UserDocsStore`, render the approved shareable summary, and call:

```python
store.create(UserDocCategory.generations, user_key, UserDocCreateRequest(
    title=f"{event.title} — Family readiness summary",
    body=render_spouse_summary(event),
    fields={"templateType": "family_readiness_summary", "familyReadinessEventId": event.event_id},
))
```

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/test_family_readiness_routes.py tests/test_user_docs.py -q`

Expected: all tests pass.

```powershell
git add app/api/routes/family_readiness.py app/services/family_readiness/calendar.py tests/test_family_readiness_routes.py
git commit -m "feat: export family readiness outputs"
```

### Task 4: Family & Deployment Readiness Advisor

**Files:**
- Modify: `app/services/agents/source_refs.py`
- Modify: `app/services/agents/readiness_development_agents.py`
- Modify: `app/services/agents/registry.py`
- Modify: `tests/test_agent_registry.py`

**Interfaces:**
- Produces: `build_family_deployment_readiness_agent() -> Agent`, ID `family-deployment-readiness-advisor`.
- Consumes: `ReadinessDevelopmentAgent`, `SourceRef` helpers.

- [ ] **Step 1: Write a failing registry test**

```python
def test_family_deployment_readiness_agent_is_registered_and_safe() -> None:
    agent = agent_registry.get("family-deployment-readiness-advisor")
    assert agent is not None
    assert category_for_agent(agent.metadata.id) == "Reserve Admin & Readiness"
    assert "power of attorney" in agent.run("Help me prepare for a 30-day AT", AgentContext()).answer.lower()
    assert "DRAFT — Verify all references" in agent.run("Help", AgentContext()).answer
    assert any("SSN" in value or "mission" in value for value in agent.metadata.disallowed_inputs)
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_agent_registry.py -q`

Expected: registry lookup returns `None`.

- [ ] **Step 3: Add official source references and builder**

Define `FAMILY_READINESS_REFERENCES` with the seven official URLs listed in the design spec and verification date `2026-07-15`. Add:

```python
def build_family_deployment_readiness_agent() -> Agent:
    return ReadinessDevelopmentAgent(
        metadata=AgentMetadata(
            id="family-deployment-readiness-advisor",
            name="Family & Deployment Readiness Advisor",
            description="Builds household-readiness checklists for extended AT through long overseas absences.",
            domain="family and deployment readiness",
            intended_users=["reserve Marines", "service members", "unit leaders"],
            allowed_sources=[ref.title for ref in FAMILY_READINESS_REFERENCES],
            disallowed_inputs=["SSNs", "dependent identity records", "medical records", "legal-document contents",
                               "mission details", "precise movement or return details", "account credentials"],
            system_prompt="Tailor local checklists using duration and broad household needs. Track actions, not sensitive contents.",
        ),
        references=FAMILY_READINESS_REFERENCES,
        answer=("Family and deployment readiness advisory draft.\n\n"
                "Use the Bench+Files readiness checklist to track unit coordination, legal-assistance review, "
                "power of attorney questions for qualified counsel, DEERS/ID-card checks, contacts, household continuity, "
                "OPSEC, and reintegration. Do not enter mission, movement, SSN, medical, account, or legal-document details.\n\n"
                "DRAFT — Verify all references against current official sources before acting."),
        questions=["What is the approximate duration?", "Which broad household responsibilities require continuity?",
                   "Which checklist areas are already complete?"],
    )
```

- [ ] **Step 4: Register, categorize, test, and commit**

Add the builder import, `_AGENT_CATEGORY_BY_ID` entry, and `default_agents()` call.

Run: `uv run pytest tests/test_agent_registry.py tests/test_agent_content_reliability.py -q`

Expected: all tests pass.

```powershell
git add app/services/agents/source_refs.py app/services/agents/readiness_development_agents.py app/services/agents/registry.py tests/test_agent_registry.py
git commit -m "feat: add family readiness advisor"
```

### Task 5: Bench+Files UI and browser flow

**Files:**
- Modify: `scripts/patch_dashboard_bundle.py`
- Regenerate: `app/static/dashboard/index.html`
- Modify: `tests/test_dashboard.py`
- Modify: `tests/e2e/test_dashboard_flows.py`

**Interfaces:**
- Consumes: `/family-readiness/{user_key}` API and existing User Docs generation reload.
- Produces: final Staff Products tile and event modal/editor.

- [ ] **Step 1: Add failing dashboard assertions**

```python
def test_dashboard_contains_family_readiness_tile_and_event_controls() -> None:
    component_source = dashboard_html()
    assert "Family &amp; Deployment Readiness" in component_source
    assert 'fetch("/family-readiness/"' in component_source
    assert "Start readiness checklist" in component_source
    assert "Download calendar" in component_source
    assert "Generate spouse-friendly summary" in component_source
```

Add a Playwright flow that opens Bench+Files, clicks the tile, creates `Extended AT 2027`, marks one item complete, closes the modal, reopens it, and verifies the saved state.

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_dashboard.py::test_dashboard_contains_family_readiness_tile_and_event_controls -q`

Expected: assertion failure because the tile is absent.

- [ ] **Step 3: Add idempotent dashboard patches**

Add component state for `familyReadinessEvents`, `activeFamilyReadinessEventId`, loading/status fields, and create form values. Add `_loadFamilyReadiness`, `createFamilyReadinessEvent`, `updateFamilyReadinessItem`, `openFamilyReadinessIcs`, and `generateFamilyReadinessSummary` methods using `_apiHeaders()` and `this.userKey`.

The tile definition must be exactly:

```javascript
{ kind: "Staff product", title: "Family & Deployment Readiness",
  desc: "Saved checklists for extended AT, training, mobilization, and long overseas absences.",
  output: "Checklist + calendar", templateType: "family_readiness" }
```

The modal must list saved events, show item status and ordering controls, support user-created items, contacts, event-specific glossary terms, and milestone date edits, display official links as external, and keep private notes out of the summary action. Reuse existing card/modal styles and per-action status copy.

- [ ] **Step 4: Regenerate and run focused UI tests**

Run: `uv run python scripts/patch_dashboard_bundle.py`

Expected: patch script completes successfully.

Run: `uv run pytest tests/test_dashboard.py tests/e2e/test_dashboard_flows.py -q`

Expected: dashboard assertions and browser flow pass.

- [ ] **Step 5: Verify patch idempotence and commit**

Run twice: `uv run python scripts/patch_dashboard_bundle.py`

Expected: both runs succeed and the second run produces no Git diff.

```powershell
git add scripts/patch_dashboard_bundle.py app/static/dashboard/index.html tests/test_dashboard.py tests/e2e/test_dashboard_flows.py
git commit -m "feat: add family readiness bench workflow"
```

### Task 6: Full family-readiness validation

**Files:**
- Modify only files implicated by failures.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: independently releasable Family Readiness feature.

- [ ] **Step 1: Run family and adjacent regression tests**

Run: `uv run pytest tests/test_family_readiness_builder.py tests/test_family_readiness_store.py tests/test_family_readiness_routes.py tests/test_agent_registry.py tests/test_dashboard.py tests/test_user_docs.py tests/test_calendar_planner.py -q`

Expected: all pass.

- [ ] **Step 2: Run static checks**

Run: `uv run mypy app tests`

Expected: no errors.

Run: `uv run ruff check .`

Expected: no errors.

- [ ] **Step 3: Run full tests and inspect the browser flow**

Run: `uv run pytest tests/ -q`

Expected: full suite passes with only the repository's documented skips/deselections.

Run: `uv run pytest tests/e2e/test_dashboard_flows.py -q`

Expected: all dashboard browser flows pass.

- [ ] **Step 4: Review the final diff and record any cohesion fix**

Run: `git status --short`

Expected: clean when validation required no fix. If validation required a fix, verify every changed path belongs to Family Readiness, stage each verified path explicitly, and commit with `git commit -m "fix: harden family readiness workflow"`. Do not create an empty commit.
