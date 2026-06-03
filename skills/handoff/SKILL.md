---
name: handoff
description: Write a handoff document summarising the current session so a fresh agent or new session can continue the work without re-reading the full conversation history.
---

# Handoff

## Purpose

Capture where things stand at the end of a session — what was done, what is open, and what the next agent needs to know to pick up cleanly.

## When To Use

- End of a long work session before closing Claude Code.
- Before handing off to Codex or another AI tool to continue a task.
- When switching context and wanting to preserve thread without re-reading history.
- Before a drill weekend or gap period when you will resume later.

## Output

Save the handoff document to the OS temp directory, **not** the current workspace. Do not commit it.

The document should include:

1. **What was accomplished** — specific files changed, tasks completed, commits pushed.
2. **What is open** — incomplete tasks, blocked items, pending decisions.
3. **Key decisions made** — choices that should not be revisited without reason.
4. **Suggested next steps** — ordered by priority with brief rationale.
5. **Suggested skills** — which skills the next agent should load for the work ahead.
6. **Repo state** — current branch, test status, any uncommitted changes.

## Rules

- Do not include API keys, passwords, local file paths outside the repo, or personal data.
- Do not duplicate content already in committed files — reference them by path instead.
- Keep it short enough to be read in under 2 minutes.
- If the user provides a focus area for the next session, tailor the document to that context.

## Preferred Repo Paths

This skill does not call repo routes. It summarises session state for human and agent handoff.

For structured session continuity within the repo, see:
- `POST /handoffs/{user_key}` — store a session handoff record
- `GET /chief/brief/{user_key}` — surface handoff-driven brief on next load
