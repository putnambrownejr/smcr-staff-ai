---
name: connector-adapter
description: Use when external calendar events or email summaries have been collected outside the repo and need to be translated into Chief/Aide, handoff, and action-ready local shapes. Does not perform connector auth or live mailbox reads — it adapts already-collected summaries into repo-native workflows. Triggers on phrases like "I got these calendar items," "here's what my email says," "turn this into a chief brief," "adapt these events," "I exported my calendar," or any time the user hands over external scheduling or email content and wants it normalized into the repo's planning and action workflows.
---

# Connector Adapter

## Purpose

Bridge the gap between externally-collected calendar events or email summaries and the repo's native Chief/Aide, handoff, and action-tracking workflows. The repo doesn't own OAuth or live connector access — this skill is for the moment after the user has already gathered the inputs from their calendar or mailbox, and needs them turned into actionable reserve-workflow shapes.

The key distinction: the user brings the data, the skill brings the interpretation.

## When To Use

- The user has pasted or described calendar events (drill dates, meetings, suspense items) and wants them turned into a Chief brief and action tracker entries.
- The user has email summaries or subject lines and wants them triaged into handoff updates, admin due-outs, or promoted actions.
- A calendar or email plugin has surfaced events/messages and the user wants them normalized into reserve-staff context.
- The user wants to update their session handoff with new information from external sources without manually editing the handoff JSON.

## When Not To Use

- When no external inputs have been provided — don't guess at calendar or email content.
- When the user needs live mailbox or calendar access — this skill works only with content the user provides directly.
- When the user wants a Chief brief from stored local handoff data alone (use `chief-brief-ops` instead).
- When the email or calendar content contains classified, CUI, or sensitive operational details — decline and note the constraint.

## Preferred Repo Paths

**Build a connector digest plan from provided inputs:**
- `POST /connectors/chief-digest-plan` — takes consents + user-provided calendar events + email messages; returns read plans and action items

**Full workflow adapter (preferred when inputs are ready):**
- `POST /connectors/workflow-adapter` — takes the same inputs and returns:
  - A Chief/Aide digest
  - A `handoff_draft_request` ready for `/handoffs/{user_key}/draft-update`
  - An `action_promote_request` ready for `/actions/promote`

**Draft and apply handoff updates:**
- `POST /handoffs/{user_key}/draft-update` — propose structured updates from notes
- `POST /handoffs/{user_key}/apply-update` — apply a confirmed patch (user must confirm first)

**Promote actions:**
- `POST /actions/promote` — turn due-outs into tracked action items

**Travel case accumulation (from email travel summaries):**
- Routes in `/connectors/` also surface travel cases — DTS/GTCC follow-through survives across multiple email inputs

## Workflow

1. Collect the external inputs from the user — calendar event summaries, email subject lines, or pasted message content.
2. Confirm consent state: what providers does the user consider active, and what access mode (read-only is the safe default).
3. Format the inputs into the `ConnectorWorkflowAdapterRequest` schema: consents array, calendar_events array, email_messages array.
4. Call `POST /connectors/workflow-adapter` — this is the single best entry point that produces all three outputs in one pass.
5. Surface the Chief/Aide digest output for the user to review.
6. Present the `handoff_draft_request` — ask the user to confirm before applying it to the stored handoff.
7. If the user confirms, call `POST /handoffs/{user_key}/apply-update` with the confirmed patch.
8. Present the `action_promote_request` — ask the user to confirm before promoting.
9. If the user confirms, call `POST /actions/promote` to create tracked action items from the due-outs.

Always keep the two-step confirm pattern for handoff updates and action promotion — the skill proposes, the user approves.

## Output Format

- **Chief/Aide digest** — triage brief built from the provided calendar and email inputs.
- **Handoff draft** — structured update proposal for PME, FitRep, admin watch items, and recurring checks; labeled as a draft pending user confirmation.
- **Action candidates** — due-outs and action items extracted from the inputs; labeled as pending promotion until user confirms.
- **Travel case summary** — any DTS/GTCC or CI Travel items surfaced from email content, with follow-through prompts.
- **Consent summary** — which providers were treated as active for this pass.

## Safety And Review Rules

- This skill performs no live connector reads — it works only with content the user explicitly provides.
- Do not invent calendar events or email content not present in the user's input.
- Always present handoff updates as drafts and require explicit user confirmation before applying them.
- Always present action promotions as candidates and require explicit user confirmation before promoting.
- Keep all output UNCLASSIFIED — if the user's input contains sensitive operational details, decline to process and note the constraint.
- Treat calendar and email content as advisory context, not authoritative command information.

## Failure Modes

- User provides vague event summaries without dates or suspense — flag the ambiguity rather than guessing.
- Email subjects don't contain enough context to infer action items — surface what was parsed and mark the rest as unclear.
- Handoff draft proposes changes the user didn't intend — always show the diff before applying.
- Travel case data is incomplete — note what's missing (voucher due date, rental car, receipts) and prompt the user to supply it.

## Verification Checklist

- All user-provided calendar events and email items appear in the digest output — nothing was silently dropped.
- Handoff update is shown as a draft, not applied automatically.
- Action promotions are shown as candidates, not promoted automatically.
- Travel items (if present) have follow-through prompts for DTS/GTCC completion.
- Consent state is explicitly noted — no live reads were claimed.
