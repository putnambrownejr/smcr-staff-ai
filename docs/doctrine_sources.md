# Doctrine Sources

The project uses `data/seed/doctrine_manifest.example.yaml` to describe source categories without embedding large source texts.

Preferred source metadata:

- title
- publication type
- issuing organization
- public URL
- version or date
- classification label
- CUI flag
- retrieval date
- source hash when fetched

Use official public sources where possible. Preserve effective dates and versioning so future RAG responses can cite current material and warn when documents may be stale.

Quick-reference Markdown files live in `docs/sources/`. These files should contain links, metadata, usage notes, and ingestion guidance only. They should not contain copied publication bodies.

The repository also includes `docs/usmc_history_context.md` as a compact Marine Corps history and heritage study reference for agents and PME prompts. It is not official curriculum and should be verified against current training materials.
