# Data Governance

## Public Source Ingestion

The default ingestion posture is public, official, and UNCLASSIFIED. Store manifests and source metadata rather than bulk publication text when copyright or redistribution is unclear.

Live public-source fetches must use allowlisted official sources or explicit vetted adapters. Do not accept arbitrary user-provided URLs for server-side fetching.

## SMCR Billet Sources

Billet discovery should prefer official Marine Corps public pages such as MARFORRES billet opportunity pages and the Marine Corps Reserve Hub linked from official manpower pages. Billet data is time-sensitive and should be treated as advisory until verified through official Reserve channels. Do not store private eligibility data, protected personnel details, or sensitive career counseling notes.

## Vetted Social And News Trend Sources

Social/news trend ingestion is limited to public, lawfully accessible records supplied by a user, approved export, feed, or future explicit platform adapter. The connector normalizes topic-level trend records for citation and confidence analysis. It must not collect private messages, private profiles, personal contact information, doxxing material, credentialed data, or access-controlled content.

Future live connectors must document platform terms, authentication handling, rate limits, retention, attribution, and fixture-based tests. Social trend data must be treated as noisy signal rather than validated fact.

## Local User Context

Users may upload local working context for advisory workflows. In normal local runs, this data defaults to a user-scoped storage home outside the repo; Docker uses its own mounted or named-volume path. This storage is intentionally separate from canonical doctrine, organization, exercise, and document structures. Uploading context does not change manifests, seed data, registry metadata, or RAG source authority. Future RAG features must make local-context inclusion explicit per request and must label it as user-provided, unverified context.

RQS, BIO, and drill-plan files should be treated as user-provided local records. The prototype records `document_type`, `contains_pii`, `retention_policy`, and `consent_ack`, and redacts simple PII from previews. It does not automatically extract permanent profile facts from RQS/BIO uploads.

## CUI Placeholder

This repository is not approved for CUI. Future CUI support would require an approved environment, access controls, audit logging, retention policy, and explicit source labeling.

## PII Minimization

Do not store personal data unless absolutely required for a future approved workflow. Calendar tasks should be generic and avoid personal readiness details beyond user-provided local context.

Session handoffs should store references to local records when possible instead of copying personnel document contents. Future implementations should add encryption at rest, per-field sensitivity labels, TTLs, export/purge controls, and explicit confirmation before extracted facts update a user profile.

## Logs

Logs must not capture secrets, tokens, PII, classified content, CUI, operational details, COMSEC, keying material, frequencies, or call signs.

## Retention

Prototype local data should be disposable. Future deployments must define retention windows for documents, chunks, calendar plans, logs, and user inputs.

## Calendar Tokens

Microsoft Graph and Google Calendar providers are stubs. When implemented, tokens must be encrypted at rest, scoped narrowly, never logged, and revocable.

Connector routes currently produce consent plans and staged write-action plans only. Read/write access requires review-before-write, and full access cannot be enabled by default in this prototype.

## GitHub Secret Scanning

Enable secret scanning for public repositories. Keep `.env` ignored. Use `.env.example` with placeholder values only.

## OPSEC

Do not enter sensitive unit-specific plans, current movements, mission details, call signs, exact frequencies, COMSEC, keying material, or classified/CUI details. The app should surface OPSEC warnings in relevant workflows.
