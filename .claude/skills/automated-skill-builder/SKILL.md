---
name: automated-skill-builder
description: Mine recent Claude Code session transcripts and git logs for smcr-staff-ai to surface repeated manual work, unmet agent gaps, and automation opportunities — then draft concrete skills, agents, or automation proposals. Use when asked "what should we automate", "build me a skill", "skill harvest", or "find automation opportunities."
---

# Automated Skill Builder — smcr-staff-ai

Surface what's been done manually that a skill, agent, hook, or CLAUDE.md rule should handle instead — then draft the concrete implementation.

## When to Use

- On-demand: "what should we automate", "build a skill for X", "find automation opportunities"
- After a sprint of agent or dashboard work
- When the agent registry or skill set feels stale

## What It Mines

| Source | What to look for |
|---|---|
| Session transcripts (`~/.claude/projects/C--smcr-staff-ai/`) | Repeated tool call sequences, recurring user corrections, tasks typed more than once |
| Git log (`C:\smcr-staff-ai`) | Repeated commit patterns, manual steps in commit bodies, frequent file churn in the same areas |
| Agent registry (`app/services/agents/`) | Gaps between what users ask and what agents cover; agents never invoked; overlapping coverage |
| Project skills (`.claude/skills/`) | Skills that exist but aren't triggered; missing skills for common workflows |
| CLAUDE.md | Stale instructions, rules added to fix repeated mistakes, TODOs that recur |
| Dashboard JS (`app/static/dashboard/`) | UI patterns users complain about or work around |

## Workflow

### Phase 1 — Gather Evidence

**Session transcripts** — scan the last 7 days:

```bash
# List recent sessions for this project
find ~/.claude/projects/C--smcr-staff-ai -name "*.jsonl" -mtime -7 2>/dev/null | sort
```

**Git logs:**

```bash
git -C "C:\smcr-staff-ai" log --oneline --since="7 days ago" | head -30
```

**Agent usage gaps** — check which agents exist vs. what's been asked:

```bash
# List all registered agent IDs
grep -r 'id="' app/services/agents/ --include="*.py" -h | grep -o 'id="[^"]*"'
```

**Skill inventory:**

```bash
ls .claude/skills/
```

### Phase 2 — Pattern Analysis

Look for:

- **Repeated prompts** — same question asked 3+ times across sessions
- **Manual glue work** — copy-paste between dashboard and AI, running the same command sequences
- **Correction loops** — agent gave wrong advice, user corrected the same way repeatedly (signals a missing rule or bad agent content)
- **Agent routing misses** — users asking general questions that a specific agent should catch
- **Dashboard friction** — UI workflows that take too many clicks or confuse users
- **Missing echelon/MOS coverage** — questions about specific echelons or MOS codes that no agent handles well

### Phase 3 — Proposals

For each pattern, generate:

```
---
PROPOSAL: <short name>
Type: skill | agent-update | CLAUDE.md rule | dashboard widget | hook | custom-MOS-recipe
Priority: high | medium | low
Pattern observed: <specific evidence — file, date, frequency>
Proposed solution: <what to build or change>
Estimated effort: trivial (< 30 min) | small (1–2 hrs) | medium (half day)
Target: .claude/skills/ | app/services/agents/ | CLAUDE.md | app/static/dashboard/
Draft: <if trivial, include starter content>
---
```

Aim for 3–6 concrete proposals. More is noise.

### Phase 4 — Report

```markdown
# Automated Skill Builder Report — <YYYY-MM-DD>

## Summary
<2–3 sentences: what dominated the week, biggest gap>

## Proposals (ranked)
<3–6 proposals>

## Patterns Not Ready Yet
<seen once — log but don't act>

## Agents/Skills to Retire or Trim
<anything unused or redundant>

## Next Actions
1. <immediate>
2. <this week>
3. <backlog>
```

## Rules

- **Evidence-first.** Only propose for patterns seen at least twice.
- **Stay specific.** Name the file, the date, the exact friction.
- **Draft the trivial ones.** If effort is trivial, include the starter content.
- **Check before proposing.** Don't propose what an existing agent or skill already covers.
- **Bias toward rules first.** A CLAUDE.md rule or hook that takes 5 lines beats a full skill.
- **UNCLASSIFIED only.** Do not mine or reference any classified, CUI, or sensitive content from transcripts.
