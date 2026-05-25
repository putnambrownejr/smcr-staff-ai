# External AI Safe Use

This repo can work well with ChatGPT, Claude, Gemini, Grok, Copilot, and other hosted AI systems, but only if local user context is shared deliberately.

## Safe Principle

Share the **minimum useful context**, not the raw local record.

Good candidates to share:

- generalized billet/MOS context
- training objective
- broad unit type
- non-sensitive admin or planning friction
- MET/METL framing
- sanitized drill rhythm

Avoid sharing directly:

- names and personal identity details when not needed
- raw uploaded documents
- filenames
- local `context_id` values
- linked `rqs_context_id` / `bio_context_id`
- exact drill-event locations, movements, or sensitive timing
- raw note dumps that may contain PII or OPSEC issues
- secrets, tokens, API keys, credentials

## Share-Safe Packet

Use:

- `POST /sharing/external-ai-packet`

This route builds a scrubbed packet for external AI use and returns:

- `target_platform`
- `safe_to_share`
- warnings
- withheld categories
- redacted fields
- recommended share format
- a recommended share prompt

Supported target values:

- `generic`
- `claude`
- `gemini`
- `grok`
- `copilot`
- `genai`

Use `genai` when the target is a government-hosted or otherwise unspecified model environment and you want the most conservative prompt framing.

For provider-specific examples and starter prompts, see:

- [C:\smcr-staff-ai\docs\compatibility\external_ai_playbooks.md](C:/smcr-staff-ai/docs/compatibility/external_ai_playbooks.md)

## Why This Exists

The local memory layer is intentionally richer than what should normally leave the machine. The share-safe packet is the boundary between:

- local continuity for you
- hosted AI context for outside tools
