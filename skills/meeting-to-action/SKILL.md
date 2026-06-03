---
name: meeting-to-action
description: Use when converting meeting notes, transcripts, rough notes, or email-like text into decisions, action items, owners, suspense, open questions, and a reviewable follow-up draft. Prefer existing analysis, action, and staff-product routes before inventing a one-off workflow.
---

# Meeting To Action

## Purpose

Convert meeting notes, transcripts, or rough note dumps into decisions and actionable follow-up.

## When To Use

- After meetings.
- After drill syncs or command updates.
- After brainstorming.
- When a transcript needs cleanup into execution items.

## When Not To Use

- When exact legal, HR, medical, or policy language must be certified from an official record.
- When the input is too ambiguous to assign owners or suspense without clearly marking unknowns.

## Preferred Repo Paths

Use existing repo surfaces first:

- `POST /analysis/summarize`
- `POST /demo/analysis/summarize`
- `POST /actions/track`
- `POST /actions/from-chief-brief`
- `POST /staff-products/poam`

Use this skill to bridge from raw notes into those repo workflows rather than replacing them.

## Workflow

1. Summarize the meeting in plain language.
2. Extract decisions.
3. Extract action items with owners and deadlines.
4. List open questions and dependencies.
5. Mark uncertainty instead of guessing.
6. Draft a follow-up message if requested.
7. If useful, promote the due-outs into the local action tracker or POAM workflow.

## Output Format

- Summary.
- Decisions.
- Action items.
- Owners and deadlines.
- Open questions.
- Uncertainties.
- Follow-up draft.

## Safety And Review Rules

- Do not send follow-ups without approval.
- Do not invent owners or dates.
- Mark ambiguous transcript content clearly.
- Keep the output advisory and reviewable.

## Failure Modes

- Poor transcript quality.
- Missing names.
- Implied but unstated deadlines.
- Conflicting decisions.

## Verification Checklist

- Every action item has an owner or is marked unassigned.
- Deadlines are exact or marked unknown.
- Uncertainties are visible.
- Follow-up draft is reviewable before use.
