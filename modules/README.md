# Module Packs

Each sub-folder in this directory is a **module pack** — a shareable collection of unit-specific documents that can be activated in the dashboard and ingested into any user's local context.

## How to use

1. Create a sub-folder with a short, descriptive name (e.g. `3bn14th-unit-docs` or `exercise-iron-fist-25`).
2. Drop your files in. Supported formats: `.md`, `.txt`, `.pdf`.
3. Optionally add a `manifest.json` to give the pack a title and description (see below).
4. Open the dashboard → Bench / Files lane → **Module Packs** panel → click **Activate**.

The pack's files are stored in your local context with a `module` tag and the pack name. They appear in your Personal Files panel and are available as context for agent tools.

## Sharing a pack

Because module packs live inside the repo, they can be shared by:
- Pushing the folder to your shared git remote
- Copying the folder to a buddy's `modules/` directory
- Zipping and sending the folder — they drop it here and activate it

## manifest.json (optional)

```json
{
  "title": "3rd Bn 14th Marines Unit Reference",
  "description": "SOPs, range card templates, and admin references for 3/14.",
  "author": "HQ",
  "version": "2025-06",
  "tags": ["unit", "sop", "admin"]
}
```

If `manifest.json` is absent, the folder name is used as the title.

## Security and classification

Keep all files **UNCLASSIFIED**. Do not include CUI, classified material, COMSEC, real frequencies, or sensitive operational details. All outputs from the AI tools referencing this content are advisory drafts requiring human review.

## Supported file types

| Extension | Notes |
|-----------|-------|
| `.md` | Markdown — best format for structured notes, SOPs, and references |
| `.txt` | Plain text |
| `.pdf` | PDF — text extracted automatically |

Files over 50 MB are skipped during ingestion.
