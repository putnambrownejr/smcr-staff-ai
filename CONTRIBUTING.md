# Contributing

Thanks for helping make `smcr-staff-ai` useful and safe.

## Ground Rules

- Keep all contributions UNCLASSIFIED and public-source appropriate.
- Do not add secrets, credentials, PII, CUI, controlled technical details, real operational plans, real frequencies, COMSEC, keying material, or sensitive unit-specific data.
- Prefer official public sources and include citations or manifest entries where possible.
- Add tests for new agents, parsers, route behavior, and data models.

## Adding an Agent

See [docs/contributing-agents.md](docs/contributing-agents.md) for the full checklist
(agent file, registry, tests, dashboard dropdowns, source references).

## Running Checks

```bash
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

Run all three before opening a pull request.
