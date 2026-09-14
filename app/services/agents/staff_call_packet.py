"""Staff call packets: organize input + the right seats' lenses into a prompt for the user's AI.

This is the honest local-mode alternative to a round table. Nothing here
analyzes anything. It collects, for each seat, what the seat is for, the
questions it always asks, the products it owes, and the doctrine notes it works
from, and lays that out around the user's input so an AI assistant (Claude,
ChatGPT, Gemini, or Claude Code with this repo open) can actually convene the
staff.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.agents.base import Agent, AgentContext
from app.services.agents.staff_advisor_agent import StaffAdvisorAgent

DISCLAIMER = (
    "> **Read this first.** No AI has run and nothing below is analysis. This packet only organizes "
    "your input and the staff seats' lenses so *your* AI can convene the staff. Paste the whole packet "
    "into your AI chat (or into Claude Code / Codex with the smcr-staff-ai repo open) and it will answer "
    "as each seat, synthesize as the Chief of Staff, and draft the products. UNCLASSIFIED only."
)

_SECTION_HEADINGS: tuple[tuple[str, str], ...] = (
    ("Questions this seat always tests", "Concerns to test:"),
    ("What this seat would do next", "Recommended next action:"),
    ("What this advisor challenges", "What to challenge:"),
    ("Lenses this advisor applies", "Primary ORM lenses:"),
    ("What this advisor establishes first", "Establish first (every tempo):"),
)


def section_bullets(answer: str, heading: str, limit: int = 6) -> list[str]:
    lines = answer.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        return []
    bullets: list[str] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            if bullets:
                break
            continue
        if stripped.startswith("- "):
            if len(bullets) >= limit:
                break
            bullets.append(stripped[2:].strip())
        elif bullets and line.startswith("  "):
            bullets[-1] = f"{bullets[-1]} {stripped}"
        elif bullets:
            break
    return bullets


def _role_notes(agent: Agent) -> str:
    target = getattr(agent, "_target", agent)
    if isinstance(target, StaffAdvisorAgent):
        return target.archetype.mos_depth.strip()
    prompt = target.metadata.system_prompt or ""
    return prompt.strip()


def _seat_block(index: int, agent_id: str, agent: Agent, *, include_role_notes: bool) -> str:
    target = getattr(agent, "_target", agent)
    meta = target.metadata
    lines = [f"### {index}. {meta.name}\n\n`{agent_id}`", ""]
    if isinstance(target, StaffAdvisorAgent):
        arch = target.archetype
        lines.append(f"**Scope:** {arch.scope}")
        lines.append(f"**Lenses:** {', '.join(arch.focus)}")
        if arch.products:
            lines.append(f"**Products this seat owes:** {', '.join(arch.products)}")
    else:
        lines.append(f"**What it is for:** {meta.description}")
    # Pull the seat's standing questions from its local template (no analysis — these are fixed).
    try:
        local = target.run("Staff call packet — lens extraction only.", AgentContext(request_is_training_or_fictional=True))
        answer = local.answer
    except Exception:  # noqa: BLE001 - a seat that cannot render locally still gets its metadata
        answer = ""
    for label, heading in _SECTION_HEADINGS:
        bullets = section_bullets(answer, heading)
        if bullets:
            lines.append("")
            lines.append(f"**{label}:**")
            lines.extend(f"- {item}" for item in bullets)
    if include_role_notes:
        notes = _role_notes(agent)
        if notes:
            lines.append("")
            lines.append("<details><summary><strong>Role notes (doctrine this seat works from)</strong></summary>")
            lines.append("")
            lines.append(notes)
            lines.append("")
            lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def build_staff_call_packet(
    *,
    scenario: str,
    participants: list[tuple[str, Agent]],
    synthesizer: tuple[str, Agent] | None,
    kind: str = "roundtable",
    label: str = "",
    include_role_notes: bool = True,
    preamble: str = "",
) -> str:
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H%MZ")
    seat_names = ", ".join(agent.metadata.name for _, agent in participants)
    title = {"roundtable": "Staff call packet", "chain": "Agent chain packet", "automation": "Automation run packet"}.get(kind, "Staff call packet")
    lines = [
        f"# {title} — {label or kind} — {stamp}",
        "",
        DISCLAIMER,
        "",
        "## Your input",
        "",
        scenario.strip() or "_(no input given — paste your SITREP, question, or task here)_",
        "",
    ]
    if preamble.strip():
        lines += ["## Standing instruction (my automation)", "", preamble.strip(), ""]
    lines += ["## Instructions for the AI", ""]
    if kind == "automation":
        lines += [
            "1. Run the standing instruction above: do its steps in order, using my input for this run. If an "
            "input it needs is missing, ask for it before starting.",
            f"2. Where the steps call for a staff view, answer as each of these seats using the lenses and role notes below: {seat_names}.",
            "3. Produce the output in the format and tone the standing instruction asks for.",
            "4. Cite doctrine by publication number; mark possibly-stale facts with 'confirm current status'; UNCLASSIFIED "
            "and advisory only; end with: DRAFT — Verify all references against current official sources before acting.",
        ]
    elif kind == "roundtable":
        lines += [
            f"1. Convene these seats, in order: {seat_names}. Answer **as each seat**, using that seat's scope, "
            "lenses, standing questions, and role notes below. For each seat produce: Summary (2-4 sentences); "
            "Key concerns specific to the input; Recommendations with an owner and a time or trigger; Products "
            "this seat will build; Questions for the commander; Risks.",
            "2. Do not restate a seat's framework or role notes. Apply them to the input. Where the input lacks a "
            "fact, name it as a gap instead of inventing it.",
            "3. Then, as the "
            + (synthesizer[1].metadata.name if synthesizer else "Chief of Staff")
            + ", synthesize: bottom line; where the seats agree and disagree; decisions for the commander in "
            "priority order with deadlines; taskings by seat; one consolidated product list; open questions; "
            "risks.",
            "4. Then draft the products the synthesis lists, each as a complete advisory draft in Marine format "
            "(OPORD paragraphs, estimate sections, matrices, or naval letter as appropriate).",
            "5. Cite doctrine by publication number. Mark any organization, policy, or funding fact that may "
            "have changed with 'confirm current status'. Keep everything UNCLASSIFIED and advisory. End every "
            "product with: DRAFT — Verify all references against current official sources before acting.",
            "6. If you are running inside Claude Code or Codex with the smcr-staff-ai repo open, save each product "
            "to `projects/<project-name>/products/` as both `.md` and `.docx`, and write a session log.",
        ]
    else:
        lines += [
            f"1. Run these agents **in order**, each one reading the previous agent's output as its handoff: {seat_names}.",
            "2. For each agent, apply its lenses and role notes to the input plus everything produced so far; "
            "state what it adds, what it challenges, and what product it contributes.",
            "3. Finish with the last agent's product in full, plus a short note on what the chain could not "
            "resolve and who should answer it.",
            "4. Cite doctrine by publication number; flag possibly-stale facts with 'confirm current status'; "
            "UNCLASSIFIED and advisory only; end with: DRAFT — Verify all references against current official "
            "sources before acting.",
        ]
    lines += ["", f"## Seats at the table ({len(participants)})", ""]
    for index, (agent_id, agent) in enumerate(participants, start=1):
        lines.append(_seat_block(index, agent_id, agent, include_role_notes=include_role_notes))
    if synthesizer is not None and kind == "roundtable":
        agent_id, agent = synthesizer
        lines.append("## Synthesizer")
        lines.append("")
        lines.append(_seat_block(len(participants) + 1, agent_id, agent, include_role_notes=include_role_notes))
    lines += [
        "---",
        "",
        "DRAFT — Verify all references against current official sources before acting.",
        "",
    ]
    return "\n".join(lines)
