# Recommended Next Build Prompt

You are Codex acting as a senior full-stack engineer, AI/RAG architect, and security reviewer. Continue `smcr-staff-ai` by implementing Phase 1: MARADMIN + MCPEL ingestion.

Requirements:

- Add live fetchers behind explicit commands; tests must use fixtures only.
- Persist normalized message records with source hashes and retrieved timestamps.
- Add doctrine manifest validation.
- Add route/service tests for ingestion dry-run and local fixture ingestion.
- Preserve UNCLASSIFIED-only guardrails and do not add publication text directly to the repo.
- Expand SMCR billet discovery with a browser-capable Reserve Hub adapter only if it can be tested with fixtures and does not store sensitive personal data.
- Run `ruff check .`, `mypy app tests`, and `pytest`.
