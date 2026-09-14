"""Per-user automation store, starter templates, and the portable block renderer."""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.automations import Automation, AutomationTemplate, AutomationUpsertRequest
from app.schemas.chief_setup import ChiefSetup
from app.services.chief.setup_store import _clean_list
from app.services.session.handoff_store import is_valid_user_key

AUTOMATION_TEMPLATES: tuple[AutomationTemplate, ...] = (
    AutomationTemplate(
        key="post_drill_admin_sweep",
        name="Post-drill admin sweep",
        purpose="Close the admin loop within five days of drill so pay, travel, and corrections do not wait 28 days.",
        trigger="Within 5 days after each drill weekend",
        cadence="Monthly, after drill",
        agents=["chief-of-staff", "staff-s1", "gtcc-advisor"],
        steps=[
            "Check each traveler's DTS voucher status against the drill dates I give you and list who still owes one.",
            "Confirm Drill Manager attendance posted for every Marine who mustered; flag mismatches by name only.",
            "List open admin corrections (unit diary, MOL, awards, FitRep counseling) with owner and suspense.",
            "Produce a due-out tracker I can paste into the next handoff note.",
        ],
        inputs_needed=["Drill dates", "Attendance or muster issues", "Known travel claims and GTCC questions"],
        output_format="Due-out tracker (table: item, owner, suspense, system) plus a five-line summary",
    ),
    AutomationTemplate(
        key="pre_drill_readiness",
        name="Pre-drill readiness check",
        purpose="Front-load the friction so first formation starts ready.",
        trigger="T-14 to T-7 before each drill",
        cadence="Monthly, before drill",
        agents=["chief-of-staff", "staff-s1", "staff-s4", "staff-surgeon", "staff-sel"],
        steps=[
            "Walk the pre-drill timeline (T-14 to T-1) against the training plan I give you and list what is not done.",
            "Identify orders, range, ammo, transportation, and medical-standby suspenses that have not landed.",
            "Give the SEL a formation, accountability, and uniform-of-the-day check.",
            "Produce a readiness checklist by section with owners and a no-later-than for each item.",
        ],
        inputs_needed=[
            "Drill date and the training plan or schedule",
            "Roster changes since last drill",
            "Counts of medical or dental delinquencies (counts only, no names or PII)",
        ],
        output_format="Readiness checklist by section (S-1, S-3, S-4, Medical, SEL) with owners and NLT dates",
    ),
    AutomationTemplate(
        key="maradmin_watch",
        name="MARADMIN watch",
        purpose="Turn the message traffic I paste into actions before it bites.",
        trigger="Weekly, or whenever I paste new MARADMINs",
        cadence="Weekly",
        agents=["chief-of-staff", "staff-s1", "staff-sel"],
        steps=[
            "Review the MARADMIN numbers, titles, or text I give you.",
            "Flag anything that changes reserve pay, PME, promotion, uniforms, training, travel, or awards for my unit.",
            "Turn each flagged item into a one-line action with an owner and a date.",
            "Mark anything you are not sure is current with 'confirm current status'.",
        ],
        inputs_needed=["MARADMIN numbers, titles, or pasted text", "My unit type and billet if not in my Chief of Staff setup"],
        output_format="Table: MARADMIN · what changed · who it affects · action · owner · date",
    ),
    AutomationTemplate(
        key="aar_to_next_drill",
        name="AAR into next drill",
        purpose="Make sure what we learned changes the next event instead of dying in the AAR.",
        trigger="Within 72 hours after a training event",
        cadence="After each event",
        agents=["assessment-learning-advisor", "staff-opso", "orm-risk-management"],
        steps=[
            "Sort my observations into execution problems and event-design problems.",
            "Write a corrective-action register: observation, standard or measure, root cause, action, owner, suspense.",
            "Propose the specific changes to the next drill's training schedule and ORM worksheet.",
            "State the next-drill verification condition for each corrective action.",
        ],
        inputs_needed=["AAR notes or observations", "Next drill date and planned events", "The T&R events or METs the event was meant to train"],
        output_format="Corrective-action register (table) plus proposed schedule changes",
    ),
    AutomationTemplate(
        key="fitrep_suspense_chase",
        name="FitRep suspense chase",
        purpose="Keep reports inside the submission window and reporting seniors reminded.",
        trigger="Monthly, first week",
        cadence="Monthly",
        agents=["staff-s1", "writing-briefing-coach"],
        steps=[
            "From the roster I give you, list every report due in the next 60 days with occasion, ending date, RS, and RO.",
            "Flag any report already past its submission window.",
            "Draft a reminder message to each RS stating exactly what is needed and by when.",
            "Offer Section I writing help for any report the RS says is stuck.",
        ],
        inputs_needed=["Roster with report occasions and ending dates (names and ranks only, no SSNs or EDIPIs)"],
        output_format="Suspense table plus a reminder message draft per reporting senior",
    ),
    AutomationTemplate(
        key="range_day_package",
        name="Range day package",
        purpose="Land the four suspenses that make or break a live-fire drill.",
        trigger="T-60 before a live-fire or range event",
        cadence="Per event",
        agents=["staff-opso", "orm-risk-management", "staff-s4", "staff-surgeon", "staff-sja"],
        steps=[
            "Build the suspense timeline: RFMSS range request, Class V(W) request through the ASP, MROWS orders for OIC/RSO, medical standby.",
            "Draft the ORM worksheet with initial and residual RAC and the acceptance authority.",
            "List support requests (transportation, chow, water, comm, medical) with no-later-than dates.",
            "Write the no-go criteria and the range safety brief outline.",
        ],
        inputs_needed=["Event date, range or installation, weapons and rounds or DODIC forecast, headcount", "Any known constraints (weather window, ammo cut, personnel)"],
        output_format="Range package checklist (table) plus an ORM worksheet draft",
    ),
)


def template_by_key(key: str) -> AutomationTemplate | None:
    return next((template for template in AUTOMATION_TEMPLATES if template.key == key), None)


class AutomationStore:
    """File-per-user JSON store holding that user's automations."""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def list_all(self, user_key: str) -> list[Automation]:
        return self._read(user_key)

    def get(self, user_key: str, automation_id: str) -> Automation | None:
        return next((item for item in self._read(user_key) if item.id == automation_id), None)

    def create(self, user_key: str, request: AutomationUpsertRequest) -> Automation:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        items = self._read(user_key)
        automation = Automation(id=secrets.token_hex(6), user_key=user_key, **_normalized(request))
        items.append(automation)
        self._write(user_key, items)
        return automation

    def update(self, user_key: str, automation_id: str, request: AutomationUpsertRequest) -> Automation | None:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
        items = self._read(user_key)
        for index, existing in enumerate(items):
            if existing.id == automation_id:
                updated = existing.model_copy(update={**_normalized(request), "updated_at": datetime.now(UTC)})
                items[index] = updated
                self._write(user_key, items)
                return updated
        return None

    def delete(self, user_key: str, automation_id: str) -> bool:
        items = self._read(user_key)
        kept = [item for item in items if item.id != automation_id]
        if len(kept) == len(items):
            return False
        self._write(user_key, kept)
        return True

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root_dir / f"{digest}.json"

    def _read(self, user_key: str) -> list[Automation]:
        if not is_valid_user_key(user_key):
            return []
        path = self._path(user_key)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [Automation.model_validate(item) for item in payload.get("automations", [])]

    def _write(self, user_key: str, items: list[Automation]) -> None:
        payload = {"automations": [item.model_dump(mode="json") for item in items]}
        self._path(user_key).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalized(request: AutomationUpsertRequest) -> dict[str, object]:
    return {
        "name": request.name.strip(),
        "purpose": request.purpose.strip(),
        "trigger": request.trigger.strip(),
        "cadence": request.cadence.strip(),
        "agents": list(dict.fromkeys(agent.strip() for agent in request.agents if agent.strip())),
        "steps": _clean_list(request.steps),
        "inputs_needed": _clean_list(request.inputs_needed),
        "output_format": request.output_format.strip() or "Bullet summary with a table of actions",
        "tone": request.tone.strip() or "Direct and professional",
        "standing_notes": request.standing_notes.strip(),
        "template_key": request.template_key,
    }


def build_automation_block(
    automation: Automation,
    *,
    chief_setup: ChiefSetup | None,
    seat_lines: list[str],
) -> str:
    """Render an automation into a copy-paste standing instruction for any chatbot.

    ``seat_lines`` are "Name — scope" strings for the seats the automation consults,
    resolved by the caller from the agent registry so this module stays storage-only.
    """
    lines: list[str] = [f'You are running my "{automation.name}" automation for reserve Marine Corps staff work.']
    if automation.purpose:
        lines.append(automation.purpose)
    lines.append("")
    lines.append("## When this runs")
    if automation.trigger:
        lines.append(f"- Trigger: {automation.trigger}")
    if automation.cadence:
        lines.append(f"- Cadence: {automation.cadence}")
    if not automation.trigger and not automation.cadence:
        lines.append("- Whenever I start a message with the automation name.")

    if chief_setup is not None:
        context_rows = [
            ("Unit", chief_setup.unit),
            ("Billet", chief_setup.billet),
            ("Echelon", chief_setup.echelon),
            ("Drill schedule", chief_setup.drill_schedule),
            ("Commander's intent / focus", chief_setup.commander_intent),
        ]
        rows = [f"- {label}: {value}" for label, value in context_rows if value]
        if rows:
            lines.append("")
            lines.append("## My context (from my Chief of Staff setup)")
            lines.extend(rows)

    if automation.steps:
        lines.append("")
        lines.append("## Steps (do these in order)")
        lines.extend(f"{index}. {step}" for index, step in enumerate(automation.steps, start=1))

    if seat_lines:
        lines.append("")
        lines.append("## Consult these staff seats and answer from each lens")
        lines.extend(f"- {line}" for line in seat_lines)

    lines.append("")
    lines.append("## Inputs I will give you when I run this")
    if automation.inputs_needed:
        lines.extend(f"- {item}" for item in automation.inputs_needed)
    else:
        lines.append("- Whatever I paste with the run; ask for anything missing before you start.")
    lines.append("- If an input is missing, ask for it first instead of guessing.")

    lines.append("")
    lines.append("## Output")
    lines.append(f"- Format: {automation.output_format}")
    lines.append(f"- Tone: {automation.tone}")
    if automation.standing_notes:
        lines.append(f"- Standing notes: {automation.standing_notes}")
    lines.append("- Cite Marine Corps references by publication number; mark anything possibly out of date with 'confirm current status'.")

    lines.append("")
    lines.append(
        "UNCLASSIFIED only. Do not ask for or use classified information, CUI, COMSEC, real frequencies, "
        "call signs, or unnecessary PII. Everything you produce is an advisory draft I will verify against "
        "current official sources before acting. End with: DRAFT — Verify all references against current "
        "official sources before acting."
    )
    return "\n".join(lines)
