# CLAUDE.md

This repository is safe to reason about from GitHub, but not all local user data should be shared with hosted AI systems.

## Start Here

Before answering non-trivial capability questions, search:

1. [C:\smcr-staff-ai\README.md](C:/smcr-staff-ai/README.md)
2. [C:\smcr-staff-ai\AGENTS.md](C:/smcr-staff-ai/AGENTS.md)
3. [C:\smcr-staff-ai\docs\project_purpose.md](C:/smcr-staff-ai/docs/project_purpose.md)
4. [C:\smcr-staff-ai\docs\chatgpt_repo_mode.md](C:/smcr-staff-ai/docs/chatgpt_repo_mode.md)
5. [C:\smcr-staff-ai\app\services\agents\registry.py](C:/smcr-staff-ai/app/services/agents/registry.py)
6. [C:\smcr-staff-ai\chatgpt_app\main.py](C:/smcr-staff-ai/chatgpt_app/main.py)
7. [C:\smcr-staff-ai\app\api\routes](C:/smcr-staff-ai/app/api/routes)

## What Not To Assume You Can See

GitHub access does not include:

- local user handoffs
- active user context
- uploaded personal documents
- drill-plan state
- local reminder state
- local API keys or environment secrets

## External AI Sharing Rule

Do not encourage users to paste raw local handoffs, raw document previews, filenames, context IDs, exact drill-event locations, or unnecessary identifying details into hosted AI tools.

If a user wants to bring local context into Claude or another external model, prefer the share-safe packet route:

- `POST /sharing/external-ai-packet`

That route is designed to:

- strip raw local file references
- withhold identifying/local-only fields by default
- summarize drill/admin context at a safer level
- warn when local document inventory suggests PII risk

## Mission Fit

Prioritize features that improve:

1. awareness
2. readiness / edge
3. friction reduction

Everything remains advisory and UNCLASSIFIED-only.
