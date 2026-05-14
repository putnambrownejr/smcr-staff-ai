# Source Inventory Integration Plan

This file summarizes the user-provided deep research report stored at:

`docs/deep_research/source_inventory_integration_plan.md`

The report is treated as a planning/reference artifact, not as authoritative doctrine. It identifies NIPR-accessible public Marine Corps sources and proposes ingestion approaches for MARADMINs, MCPEL publications, doctrine, MARFORRES organizational data, and exercise/battle-rhythm content.

## Key Source Areas

### MARADMINs And ALMARs

- Source page: https://www.marines.mil/News/Messages/MARADMINS/
- Suggested ingestion:
  - Prefer RSS for discovery where available.
  - Parse listing pages for archive/backfill.
  - Use print-friendly article views for cleaner body extraction when needed.
- Implementation notes:
  - Normalize message number, title, subject, date, link, print URL, body text, and tags.
  - Tests should use local RSS and HTML fixtures.
  - Throttle requests and avoid hidden live network calls in tests.

### MCPEL Publications

- Source page: https://www.marines.mil/News/Publications/MCPEL/
- Suggested ingestion:
  - Parse MCPEL item pages for title, type, status, SSIC, date, and PDF links.
  - Use tag pages and known source manifests for priority documents before attempting broad crawling.
  - Download PDFs only for allowlisted public publications.
- Implementation notes:
  - Preserve source URL, PDF URL, retrieval date, source hash, status/currentness, classification label, and CUI flag.
  - Avoid bulk fetching the whole library in early phases.

### Doctrine Publications

- Source strategy:
  - Use MCPEL public pages rather than CAC-protected doctrine portals.
  - Start with curated manifests for MCDPs, MCWPs, MCTPs, MCRPs, MCOs, and NAVMCs already tracked in `docs/sources/`.
- Implementation notes:
  - Text extraction should include page and paragraph metadata where possible.
  - Cite publication title, official URL, retrieval date, and section/page metadata.

### MARFORRES Unit Hierarchy

- Source page: https://www.marforres.marines.mil/Marine-Forces-Reserve-Leaders/
- Suggested ingestion:
  - Parse public hierarchy links into unit, URL, parent, command level, and component.
  - Follow unit pages only for public metadata.
- Implementation notes:
  - Store as example/public organizational awareness data.
  - Avoid collecting personal data or non-public contact details.
  - Expect HTML structure changes over time.

### Operations And Exercises

- Source page: https://www.marforres.marines.mil/News-Photos/Operations-and-Exercises/
- Suggested ingestion:
  - Parse public exercise announcement pages for exercise name, dates/months, unit types, descriptions, and related staff requirements.
  - Treat cadence as typical/advisory, not fixed.
- Implementation notes:
  - Useful for ITX, UNITAS, WTI, annual training, and exercise-prep reminders.
  - Keep confidence levels and source-required flags.

## Integration Priority

1. Add fixture-backed MARADMIN RSS and print-view parsing.
2. Add MCPEL item-page parser and PDF-link extractor.
3. Add source manifest validation for known priority publications.
4. Add MARFORRES hierarchy scraper with local fixture tests.
5. Add operations/exercises parser for public exercise pages.
6. Feed normalized outputs into RAG-ready document/chunk models.

## Safety Notes

- Public/NIPR-accessible does not mean unrestricted use.
- Do not scrape CUI-only, CAC-protected, authenticated, or private content.
- Do not collect PII or sensitive unit-specific information.
- Throttle requests and respect site load.
- Tests must not require live network access.
