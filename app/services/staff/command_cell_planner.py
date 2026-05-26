from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import CommandCellRequest, CommandCellResponse


class CommandCellPlanner:
    def build(self, request: CommandCellRequest) -> CommandCellResponse:
        sections = request.coordinating_sections or ["XO", "Chief", "Battle Captain", "S-3", "S-4", "S-6", "Medical"]
        command_cell_frame = [
            f"Supported event: {request.supported_event}",
            f"Command focus: {request.command_focus}",
            (
                "The command cell exists to keep the staff aligned on what changed, "
                "what matters, and who owns the next move."
            ),
            (
                "If the watchboard cannot show the owner, suspense, and decision trigger, "
                "the command cell is not ready."
            ),
        ]
        if request.audience:
            command_cell_frame.append(f"Supported audience / formation: {request.audience}")

        chief_focus_board = [
            (
                "Chief focus: maintain the commander's picture, keep due-outs from drifting, "
                "and force stale friction back to owners."
            ),
            "Chief focus: separate what is truly late from what is simply not yet decided.",
            "Chief focus: keep the brief and turnover aligned with the actual state of the staff fight.",
        ]
        chief_focus_board.extend(f"Section to police for drift: {section}" for section in sections[:4])

        battle_captain_watchboard = [
            "Battle captain watchboard: current status, next report, next decision, and next support break-point.",
            "Battle captain watchboard: track what changed since the last huddle instead of replaying the whole plan.",
            "Battle captain watchboard: show the commander's next look and what must be true before that look happens.",
        ]
        battle_captain_watchboard.extend(f"Named due-out to track: {item}" for item in request.due_outs[:6])

        command_update_lines = [
            "Commander update line: what changed that affects scope, timing, or risk.",
            "Commander update line: what decision is required now versus what remains staff-level friction.",
            "Commander update line: what is on track, what is late, and what will slip next if not corrected.",
        ]
        command_update_lines.extend(f"Named decision for the brief: {item}" for item in request.critical_decisions[:4])

        turnover_handoff_notes = [
            "Turnover note: current picture, next event, next suspense, and first unresolved friction.",
            "Turnover note: what changed in the last watch and what the relieving watch must verify immediately.",
            "Turnover note: what has already been elevated so the next watch does not re-litigate it from zero.",
        ]
        turnover_handoff_notes.extend(f"Constraint to keep visible: {item}" for item in request.constraints[:4])

        ccir_and_decision_triggers = [
            (
                "CCIR trigger: a support, comm, admin, or medical shortfall that changes "
                "the plan instead of merely annoying the staff."
            ),
            (
                "Decision trigger: a suspense missed far enough that command must cut scope, "
                "re-sequence, or accept risk."
            ),
            "Escalation trigger: anything that invalidates the current brief to the commander or XO.",
        ]

        return CommandCellResponse(
            title=f"Command cell support: {request.title}",
            command_cell_frame=command_cell_frame,
            chief_focus_board=chief_focus_board,
            battle_captain_watchboard=battle_captain_watchboard,
            command_update_lines=command_update_lines,
            turnover_handoff_notes=turnover_handoff_notes,
            ccir_and_decision_triggers=ccir_and_decision_triggers,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "Command-cell support is advisory only and must be reconciled with commander guidance, "
                    "actual watchstanding procedures, and current staff ownership."
                ),
            ],
        )
