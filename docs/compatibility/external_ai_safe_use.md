# External AI Safe Use

This repo works well with hosted AI tools (ChatGPT, Claude, Gemini, Grok, Copilot, government GENAI environments),
but only when local context is shared deliberately. The local memory layer is intentionally richer than what
should normally leave the machine.

---

## Safe Principle

Share the **minimum useful context**, not the raw local record.

For the app's optional scenario inference, use the built-in preview dialog. It shows
the exact original and sanitized messages before any network call. Detector matches are
advisory warnings: they can help you notice PII or operational-looking text, but they
cannot determine classification, authorization, or whether a training example is safe.
You may proceed after explicit acknowledgement when you have made that determination.
See [ADR-001](../decisions/ADR-001-user-controlled-external-processing.md).

**Safe to share:**
- Generalized billet/MOS context
- Training objective and event type
- Broad unit type (company, battalion)
- Non-sensitive admin or planning friction
- MET/METL framing
- Sanitized drill rhythm

**Avoid sharing:**
- Names and personal identity details when not needed
- Raw uploaded documents or filenames
- Local `context_id` values or linked `rqs_context_id` / `bio_context_id`
- Exact drill-event locations, movements, or sensitive timing
- Raw note dumps that may contain PII or OPSEC issues
- Secrets, tokens, API keys, or credentials

---

## Share-Safe Packet

Always build the packet first:

```
POST /sharing/external-ai-packet
```

This route returns a scrubbed output with:
- `target_platform` framing
- `safe_to_share` flag
- Warnings and withheld categories
- Redacted fields
- Recommended share prompt

Minimal example:
```json
{
  "user_key": "capt-example",
  "target_platform": "genai",
  "include_handoff": true,
  "include_active_user_context": true,
  "include_document_summary": false,
  "include_drill_plans": false,
  "include_opportunities": false,
  "purpose": "an advisory training review"
}
```

---

## Provider Playbooks

### Claude — `target_platform: "claude"`
Best for: planning review, staff-package critique, AAR cleanup, FRAGO/CONOP refinement.

Recommended:
- `include_handoff: true`, `include_active_user_context: true`
- `include_document_summary: false`, `include_drill_plans: false`

Starter prompt:
```
Use this advisory reserve-staff packet as the only local context. Help me refine the plan,
identify assumptions, and produce a cleaner staff-quality output without inventing hidden
personal details or operational specifics.
```

---

### ChatGPT / Gemini — `target_platform: "gemini"`
Best for: structured synthesis, repo-aware planning help, scenario grounding.

Recommended:
- `include_handoff: true`, `include_active_user_context: true`
- `include_drill_plans: true` (if the task requires it)

Starter prompt:
```
Use this share-safe packet as the only local context. Stay grounded in the packet,
preserve the advisory and UNCLASSIFIED posture, and help me improve the training plan,
FRAGO, CONOP, or AAR without guessing at withheld details.
```

---

### Grok — `target_platform: "grok"`
Best for: blunt critique, quick stress-testing, "what will fail first" review.

Recommended:
- `include_handoff: true`, `include_drill_plans: true`

Starter prompt:
```
Use this advisory reserve-staff packet only. Give me a practical critique of what is weak,
vague, or likely to fail, but do not infer hidden personal data, exact locations, or
sensitive details that were intentionally withheld.
```

---

### Copilot — `target_platform: "copilot"`
Best for: repo-aware implementation help, route/schema/tool suggestions.

Recommended:
- `include_handoff: true`, `include_active_user_context: true`
- `include_drill_plans: false`

Starter prompt:
```
Use this share-safe packet plus the repository context. Stay close to the existing routes,
schemas, agents, and tool surfaces. Help me implement or refine the workflow without
assuming access to raw local records.
```

---

### Government / GENAI — `target_platform: "genai"`
Best for: most conservative hosted-model use, advisory review where the exact model environment is unclear.

Recommended:
- `include_handoff: true`, `include_active_user_context: true`
- `include_document_summary: false`, `include_drill_plans: false`
- Add drill plans only if the task truly requires them and they remain generic after scrubbing.

Starter prompt:
```
Use this share-safe packet only. Keep the response UNCLASSIFIED, advisory, and conservative.
Do not infer withheld operational detail, personal data, or precise locations. Help me
improve the planning product while keeping the result suitable for human review.
```

---

## When Not to Share Externally

Do not pass the packet to a hosted AI until you clean it up further if it still contains:
- Raw names or identifiers that are not necessary
- Exact locations or movements
- Real-time operational detail
- Document contents with PII
- Credentials, access details, or local secrets

The app will not silently send any of these items. It also cannot validate your authority
to disclose them; the preview and acknowledgement preserve that decision for the user.
