"""Generate prompt-packs/round-table.md from the live agent registry.

The pack is a full-staff "staff call packet" with a placeholder where the user
pastes their SITREP or question. It lets any chatbot convene the virtual staff
without the app running. Re-run after changing seat scopes or role depth:

    uv run python scripts/build_roundtable_pack.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.agents.registry import AgentRegistry  # noqa: E402
from app.services.agents.roundtable import FULL_STAFF_PARTICIPANTS  # noqa: E402
from app.services.agents.staff_call_packet import build_staff_call_packet  # noqa: E402

PLACEHOLDER = "<<PASTE YOUR SITREP, SCENARIO, TRAINING IDEA, OR STAFF QUESTION HERE>>"

HEADER = """# SMCR Virtual Staff Round Table — AI Prompt Pack

Paste this entire file into any AI chat (ChatGPT, Claude, Gemini, Copilot) and replace the
placeholder under **Your input** with your SITREP, scenario, training idea, or question. The AI
will answer as every staff seat, synthesize as the Chief of Staff, and draft the products.

**This pack contains no analysis.** It is the seats' scopes, standing questions, products, and
doctrine notes, organized so an AI can do the staff work. The smcr-staff-ai app builds the same
packet with your text already inserted (AI page → Round table).

**UNCLASSIFIED only.** Do not paste classified info, CUI, COMSEC, real frequencies, call signs,
or sensitive operational details. All outputs are advisory drafts — verify against current
official sources before acting.

---

"""


def main() -> int:
    registry = AgentRegistry()
    participants = []
    for agent_id in FULL_STAFF_PARTICIPANTS:
        agent = registry.get(agent_id)
        if agent is None:
            raise SystemExit(f"Unknown agent {agent_id}")
        participants.append((agent_id, agent))
    synthesizer = registry.get("chief-of-staff")
    assert synthesizer is not None
    packet = build_staff_call_packet(
        scenario=PLACEHOLDER,
        participants=participants,
        synthesizer=("chief-of-staff", synthesizer),
        kind="roundtable",
        label="full staff",
        include_role_notes=True,
    )
    # The pack header replaces the packet's own title line.
    body = packet.split("\n", 1)[1].lstrip("\n")
    out = ROOT / "prompt-packs" / "round-table.md"
    out.write_text(HEADER + body, encoding="utf-8")
    print(f"Wrote {out} ({len(HEADER + body):,} chars, {len(participants)} seats)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
