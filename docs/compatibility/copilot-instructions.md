# GitHub Copilot Repository Instructions

This repository exists to help Marine Corps Reservists stay aware, stay sharp, and reduce reserve-service friction through advisory staff workflows. Outputs are drafts, not command authority.

## Search Before You Answer

Before answering non-trivial questions about repo capability, workflow, or implementation, search:

1. `README.md`
2. `AGENTS.md`
3. `docs/core_documents/project_purpose.md`
4. `docs/compatibility/ai_assistant_guide.md`
5. `app/api/routes/`
6. `app/services/agents/registry.py`
7. `docs/examples/`

Do not answer from vague memory alone when the repo can be searched directly.

## Capability Preference

Prefer this order:

1. existing app tools
2. existing repo agents and workflows
3. existing routes and schemas
4. new code only if the capability is genuinely missing

Do not rebuild commodity email, calendar, or auth flows when the repo already intends to reuse external connectors.

## Safety And Scope

Keep everything UNCLASSIFIED.

Do not add or encourage:

- classified information
- CUI
- COMSEC or keying material
- real frequencies or call signs
- precise current movements
- unnecessary PII
- fake command authority

Treat local notes, uploaded files, and user memory as advisory context, not authoritative truth.

## External AI Context Boundary

GitHub context does not include local user handoffs, active user context, uploaded personal documents, or local reminder state.

If the user wants to take local context into Copilot Chat or another hosted AI, prefer:

- `POST /sharing/external-ai-packet`

That route creates a scrubbed packet and withholds raw local-only fields by default.
