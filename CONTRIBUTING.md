# Contributing

Thanks for helping make `smcr-staff-ai` useful and safe.

## Ground Rules

- Keep all contributions UNCLASSIFIED and public-source appropriate.
- Do not add secrets, credentials, PII, CUI, controlled technical details, real operational plans, real frequencies, COMSEC, keying material, or sensitive unit-specific data.
- Prefer official public sources and include citations or manifest entries where possible.
- Add tests for new agents, parsers, route behavior, and data models.

## Adding an Agent

1. Create a new file in `app/services/agents/`.
2. Define metadata, guardrails, allowed sources, and disallowed inputs.
3. Register the builder in `app/services/agents/registry.py`.
4. Add manifest metadata in `data/seed/agent_registry.example.yaml`.
5. Add doctrine source mappings in `data/seed/doctrine_manifest.example.yaml`.
6. Add tests.

Run `ruff check .`, `mypy app tests`, and `pytest` before opening a pull request.
