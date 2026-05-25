# External AI Playbooks

This guide shows the simplest safe way to use `smcr-staff-ai` with hosted AI tools without pasting raw local records.

Use the share-safe packet route first:

- `POST /sharing/external-ai-packet`

Or use the app tool:

- `build_external_ai_packet`

## Shared Rule

For every provider:

1. build the packet first
2. share only the packet, not the raw local handoff or uploaded files
3. keep the request advisory and UNCLASSIFIED
4. do not add exact movements, real frequencies, call signs, credentials, or unnecessary PII

## Claude

Use:

- `target_platform: "claude"`

Best for:

- planning review
- staff-package critique
- AAR cleanup
- FRAGO / CONOP refinement

Recommended includes:

- `include_handoff: true`
- `include_active_user_context: true`
- `include_document_summary: false`
- `include_drill_plans: false`
- `include_opportunities: false`

Starter ask:

```text
Use this advisory reserve-staff packet as the only local context. Help me refine the plan, identify assumptions, and produce a cleaner staff-quality output without inventing hidden personal details or operational specifics.
```

## Gemini

Use:

- `target_platform: "gemini"`

Best for:

- structured synthesis
- repo-aware planning help
- scenario grounding with current public context

Recommended includes:

- `include_handoff: true`
- `include_active_user_context: true`
- `include_document_summary: false`
- `include_drill_plans: true`
- `include_opportunities: false`

Starter ask:

```text
Use this share-safe packet as the only local context. Stay grounded in the packet, preserve the advisory and UNCLASSIFIED posture, and help me improve the training plan, FRAGO, CONOP, or AAR without guessing at withheld details.
```

## Grok

Use:

- `target_platform: "grok"`

Best for:

- blunt critique
- quick stress-testing
- practical “what will fail first” review

Recommended includes:

- `include_handoff: true`
- `include_active_user_context: true`
- `include_document_summary: false`
- `include_drill_plans: true`
- `include_opportunities: false`

Starter ask:

```text
Use this advisory reserve-staff packet only. Give me a practical critique of what is weak, vague, or likely to fail, but do not infer hidden personal data, exact locations, or sensitive details that were intentionally withheld.
```

## Copilot

Use:

- `target_platform: "copilot"`

Best for:

- repo-aware implementation help
- code-adjacent workflow changes
- route/schema/tool suggestions

Recommended includes:

- `include_handoff: true`
- `include_active_user_context: true`
- `include_document_summary: false`
- `include_drill_plans: false`
- `include_opportunities: false`

Starter ask:

```text
Use this share-safe packet plus the repository context. Stay close to the existing routes, schemas, agents, and tool surfaces. Help me implement or refine the workflow without assuming access to raw local records.
```

## GENAI / government-hosted environment

Use:

- `target_platform: "genai"`

Best for:

- the most conservative hosted-model use
- advisory review where the exact model environment is unclear
- situations where you want stricter prompt framing by default

Recommended includes:

- `include_handoff: true`
- `include_active_user_context: true`
- `include_document_summary: false`
- `include_drill_plans: false`
- `include_opportunities: false`

Add drill plans only if the task truly requires them and they remain generic enough after scrubbing.

Starter ask:

```text
Use this share-safe packet only. Keep the response UNCLASSIFIED, advisory, and conservative. Do not infer withheld operational detail, personal data, or precise locations. Help me improve the planning product while keeping the result suitable for human review.
```

## Other reservist users

Default recommendation for a new user:

1. set a `user_key`
2. save active context if needed
3. build `next_drill_readiness` or a `staff_package`
4. if they want outside-model help, build `external_ai_packet`
5. choose `gemini`, `claude`, `grok`, `copilot`, or `genai` based on the actual tool they have

## Minimal packet example

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

## When not to share externally

Do not use hosted AI for the task until you clean it up further if the packet still depends on:

- raw names or identifiers that are not necessary
- exact locations or movements
- real-time operational detail
- document contents that contain PII
- credentials, access details, or local secrets
