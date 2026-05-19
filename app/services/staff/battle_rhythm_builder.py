from __future__ import annotations

from collections.abc import Sequence

from app.schemas.battle_rhythm import BattleRhythmBoardUpsertRequest, BattleRhythmEntryInput
from app.schemas.staff_updates import PlanningCellResponse


class BattleRhythmBuilder:
    def from_planning_cell(self, planning_cell: PlanningCellResponse) -> BattleRhythmBoardUpsertRequest:
        mission_analysis = planning_cell.mission_analysis
        update_cycle = planning_cell.update_cycle
        return BattleRhythmBoardUpsertRequest(
            board_title=planning_cell.title,
            source_title=planning_cell.title,
            focus=_dedupe_strings(
                [
                    planning_cell.planning_approach.decision,
                    mission_analysis.mission_statement,
                    *(update_cycle.running_estimate.command_summary or [])[:2],
                ]
            ),
            assumption_log=[
                BattleRhythmEntryInput(
                    text=item,
                    section="OPT",
                    status="open",
                    source="planning_cell",
                )
                for item in planning_cell.assumption_log
            ],
            commander_decision_log=[
                BattleRhythmEntryInput(
                    text=item,
                    section="Command",
                    status="pending",
                    source="planning_cell",
                )
                for item in planning_cell.commander_decision_log
            ],
            question_log=[
                BattleRhythmEntryInput(
                    text=item,
                    section="Staff",
                    status="open",
                    source="mission_analysis",
                )
                for item in mission_analysis.information_requirements
            ],
            due_out_board=[
                _due_out_entry(item)
                for item in planning_cell.due_out_board
            ],
            next_touchpoint=_first_or_none(planning_cell.next_opt_actions),
            context_note=_first_or_none(mission_analysis.command_frame),
            warnings=_dedupe_strings([*planning_cell.warnings]),
        )


def _due_out_entry(text: str) -> BattleRhythmEntryInput:
    section = None
    if ":" in text:
        candidate, _rest = text.split(":", 1)
        if candidate.strip():
            section = candidate.strip()
    return BattleRhythmEntryInput(
        text=text,
        section=section,
        status="open",
        source="planning_cell",
    )


def _dedupe_strings(items: Sequence[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = (item or "").strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _first_or_none(items: Sequence[str]) -> str | None:
    return items[0] if items else None
