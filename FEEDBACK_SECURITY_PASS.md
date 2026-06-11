# SMCR Staff AI Feedback and Security Pass

This handoff captures additional improvement points from a repository pass using the Codex Security workflow: threat modeling, discovery, validation, and attack-path review. Scope excluded `app/static/dashboard/`, `skills/`, `PRODUCT.md`, and `ARCHITECTURE.md` per project instructions.

Current local note: the working tree already contains route-auth hardening in `app/api/routes/documents.py`, `app/api/routes/source_updates.py`, and `app/api/routes/personnel.py`, plus a context upload document-type hardening change in `app/api/routes/context.py`. Validate and commit those separately if they are intended.

## Security Summary

### SEC-1: Previously unauthenticated source-review and document mutation routes

Status: Appears patched in the current working tree; still needs dedicated regression tests and commit review.

Severity: High if the API port is reachable; Medium for a strictly private localhost prototype.

Evidence:

- `app/core/auth.py` uses `X-Local-API-Key` when `LOCAL_API_KEY` is configured.
- Before the local route changes, `app/api/routes/documents.py`, `app/api/routes/source_updates.py`, and `app/api/routes/personnel.py` did not use `LocalApiKeyDependency`.
- A TestClient validation with `LOCAL_API_KEY=expected-key` confirmed those routes were reachable without the header while `/actions` correctly returned `401`.
- After the current working-tree hardening, the same validation returned `401` for:
  - `GET /documents`
  - `POST /documents/check-updates`
  - `GET /source-updates`
  - `POST /source-updates/{candidate_id}/review`
  - `POST /personnel/products`

Why it matters:

- The source-update routes can change local review state and source-trust workflow data.
- Personnel product endpoints may process sensitive personnel text, even if they do not persist it.
- Existing document-update tests exercised these flows without auth headers, so add negative auth coverage alongside the current behavior tests.
- OWASP classifies missing or weak authentication on API capabilities as a common API risk. Source: [OWASP API2:2023 Broken Authentication](https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/).

Recommended follow-up:

- Add explicit tests that set `LOCAL_API_KEY`, call these routes without `X-Local-API-Key`, and assert `401`.
- Add success-path tests with the expected header so future route refactors do not remove protection accidentally.
- Consider an auth inventory test for mutating routes. This would have caught the gap earlier.

### SEC-2: App-wide API key is not user/object scoped

Status: Accepted prototype risk unless the app moves beyond single-user local operation.

Evidence:

- Multiple protected routes use caller-supplied identifiers such as `user_key` in paths or request bodies, including handoffs, dashboard data, section memory, travel cases, and user context.
- `LocalApiKeyDependency` proves possession of one shared local key, but it does not bind the request to a specific user identity.

Why it matters:

- With a valid shared key, any caller can request another stored `user_key` if they know or guess it.
- OWASP recommends object-level authorization checks for API object IDs. Source: [OWASP API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/).

Recommended follow-up:

- Keep the current shared-key model only for explicit single-user local deployments.
- Before multi-user, hosted, connector-backed, or network-accessible use, introduce identity-backed auth and bind storage lookups to the authenticated subject.
- Add route-level tests showing cross-user access is denied once identity exists.

### SEC-3: Sensitive-route auth is disabled by default

Status: Intentional local-prototype behavior, but risky if deployment assumptions drift.

Evidence:

- `LOCAL_API_KEY` defaults to unset in `app/core/config.py`.
- `app/core/auth.py` treats an unset key as a no-op.
- `app/main.py` logs a startup warning when the key is unset, but the app still starts.

Why it matters:

- This is acceptable for deliberate single-user localhost operation.
- It is unsafe for LAN, tunnel, container, or hosted exposure because protected routes become anonymous.
- OWASP recommends authentication for protected API resources and avoiding authentication bypass states. Source: [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

Recommended follow-up:

- Fail closed for non-demo routes outside explicit development mode, or refuse non-loopback startup unless `LOCAL_API_KEY` is set.
- Add a deployment checklist item: production/shared use requires `LOCAL_API_KEY` or a stronger identity provider.

### SEC-4: Duplicate-content uploads collide on shared context IDs

Status: Confirmed design risk from static review; add a regression test before changing behavior.

Evidence:

- `app/services/storage/local_context_store.py` derives `context_id` from `sha256(content)[:16]`.
- Metadata is stored by `context_id`, so a second upload with identical bytes can overwrite filename, tags, `document_type`, consent flags, and preview metadata for the first upload.

Why it matters:

- Content hashes are useful dedupe metadata, but they are not safe record identities when metadata can differ by uploader, purpose, or consent.
- This becomes a cross-user data integrity issue once object ownership is introduced.

Recommended follow-up:

- Use a random per-upload record ID.
- Keep SHA-256 as an internal dedupe/integrity field.
- Add tests showing identical bytes produce distinct records and preserve each record's metadata.

### SEC-5: Upload preview parsers need extraction budgets

Status: Hardening recommendation.

Evidence:

- `app/services/storage/local_context_store.py` extracts text from uploaded PDF, DOCX, Markdown, text, and JSON content.
- DOCX extraction uses ZIP parsing and reads `word/document.xml`.
- The default upload limit is 50 MB in `app/core/config.py`.

Why it matters:

- File size checks limit uploaded bytes, but compressed containers can expand significantly during parsing.
- Malformed or adversarial PDF/DOCX files can consume CPU or memory during preview extraction.
- OWASP recommends validating file uploads and constraining accepted content. Source: [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html).

Recommended follow-up:

- Cap decompressed DOCX XML bytes before parsing.
- Add per-preview character and processing limits per file type.
- Add tests for oversized ZIP entries and malformed PDF/DOCX inputs.

## Engineering Improvements

### ENG-1: Fix README onboarding drift

Status: Broken references and at least one dead command were reported by the repo-improvement pass.

Evidence:

- `README.md` points at root-level docs such as `ai_assistant_guide.md`, `external_ai_safe_use.md`, and `capability_reuse_audit.md`; the maintained copies appear under `docs/compatibility/`.
- `README.md` advertises `make check`, but no `Makefile` was observed.
- `CONTRIBUTING.md` already documents direct `ruff`, `mypy`, and `pytest` commands.

Recommended follow-up:

- Correct README links to the maintained docs.
- Replace `make check` with the actual commands, or add a real task runner.
- Add a cheap link/command smoke check once CI exists.

Why it matters:

- README is the front door for reviewers and cross-account contributors. Broken setup instructions waste the first hour.

### ENG-2: Document the cross-account GitHub handoff path in maintained docs

Status: A new untracked `docs/handoffs/` directory exists and appears purpose-built for this, but it is not yet part of the tracked repo state from this pass.

Evidence:

- `docs/handoffs/README.md` defines a one-file-per-handoff convention and index.
- The compatibility AI guide covers repo-only versus local-runtime usage, but not fork/upstream/PR/patch handoff mechanics.

Recommended follow-up:

- Adopt `docs/handoffs/` as the maintained relay point if the team likes that convention.
- Add a short maintained GitHub handoff section covering fork setup, upstream sync, patch export, PR expectations, and local/private state that must never be pushed.

Why it matters:

- The handoff path should survive account changes without relying on chat transcripts or archived session notes.

### ENG-3: Add CI for the test and quality gates

Status: No `.github/workflows` directory was present during the scan.

Recommended follow-up:

- Add a GitHub Actions workflow for Python 3.12 that runs:
  - `python -m pytest tests/ -q`
  - `python -m ruff check .`
  - `python -m mypy app tests` after confirming current mypy status
- Keep the workflow minimal until it is green locally.

Why it matters:

- The project has a large passing test suite, strict mypy config, and ruff config, but no visible CI gate to enforce them across accounts or pull requests.
- GitHub documents workflows as repository automation under `.github/workflows`. Source: [GitHub Actions workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions).

### ENG-4: Add dependency locking and dependency update automation

Status: `pyproject.toml` uses lower-bound dependencies only; no lockfile was observed.

Recommended follow-up:

- Choose one lock/update path, such as `uv.lock`, `pip-tools`, or another project-standard lock mechanism.
- Add Dependabot or another dependency update flow after the lock strategy is chosen.

Why it matters:

- Lower bounds are good for library flexibility, but they make cross-account reproduction harder.
- A lockfile plus automated updates makes security and test results easier to reproduce.

### ENG-5: Normalize test seed-data paths away from CWD assumptions

Status: Runtime CWD path bugs appear fixed, but tests still contain several `Path("data/seed/...")` lookups.

Evidence:

- `tests/test_dashboard.py`
- `tests/test_org_hierarchy.py`
- `tests/test_manifest_and_rag.py`
- `tests/test_live_reading_catalog.py`
- `tests/test_reading_catalog.py`
- `tests/test_chief_routes.py`
- `tests/test_chief_orchestrator.py`
- `tests/test_career_watch.py`
- `tests/test_system_template_catalog.py`

Recommended follow-up:

- Add a shared `repo_root` or `seed_data_dir` fixture.
- Convert tests to use `Path(__file__).resolve().parents[1] / "data" / "seed"`.

Why it matters:

- The non-root launch regression test protects runtime behavior, but CWD-sensitive tests can still hide future drift in developer environments.

### ENG-6: Complete `.env.example` storage-path guidance

Status: `.env.example` documents only part of the storage configuration surface.

Evidence:

- `Settings` supports `SMCR_STAFF_AI_HOME` and several storage directory settings.
- `.env.example` exposes only a subset of those knobs.

Recommended follow-up:

- Prefer documenting `SMCR_STAFF_AI_HOME` as the single normal override.
- If individual store overrides are supported for operators, list all first-class storage env vars together.

Why it matters:

- Partial config examples create exactly the kind of sandbox/path confusion fixed in issues #1 and #21.

### ENG-7: Centralize storage topology and store factories

Status: Storage is partly centralized in settings and partly rebuilt in routes.

Evidence:

- `configured_storage_dirs()` knows about key storage roots.
- Several routes reconstruct sibling paths or user-specific subpaths directly when creating services.

Recommended follow-up:

- Promote active user context, document updates, drill plans, opportunities, source states, and actions to first-class settings or shared factory helpers.
- Keep route dependencies thin: settings in, store/service out.

Why it matters:

- This prevents future path-default drift and keeps non-root/sandbox behavior testable.

### ENG-8: Pick one canonical document-update API surface

Status: `/documents/updates*` and `/source-updates*` overlap.

Evidence:

- Both route families hit the document update store and support status/review behavior.
- Tests cover both shapes.

Recommended follow-up:

- Pick one canonical route family.
- Keep the other as a documented compatibility alias only if clients already depend on it.

Why it matters:

- Duplicate surfaces double the auth, docs, and test burden for the same workflow.

### ENG-9: Keep `/demo/status` in sync with the demo router

Status: The status payload appears to omit `/demo/tool-catalog`.

Evidence:

- README advertises `/demo/tool-catalog`.
- The route exists in `app/api/routes/demo.py`.
- `demo_status()` does not advertise it.

Recommended follow-up:

- Derive advertised demo routes from the router where practical.
- Otherwise, assert the full expected set in `tests/test_demo_routes.py`.

Why it matters:

- Demo status should be a trusted first-stop capability map for reviewers.

### ENG-10: Clarify the vestigial database boundary in public docs

Status: Documentation follow-up only. Do not edit `ARCHITECTURE.md` in this pass because it was out of scope by instruction.

Evidence:

- `README.md` still references SQLModel database models/session setup.
- The application now treats document ingestion and the old `Document` table as future or vestigial runtime surface.

Recommended follow-up:

- Decide whether the database layer is future scaffolding or should be deleted.
- Update onboarding docs to state the decision clearly.

Why it matters:

- New contributors can otherwise spend time wiring against a table that runtime code intentionally does not use.

### ENG-11: Remove stale hard-coded repo metrics from contributor docs

Status: Low-priority documentation cleanup.

Evidence:

- Contributor docs contain exact counts such as `503+` tests and route/agent totals.

Recommended follow-up:

- Replace exact counts with qualitative wording unless CI generates them.

Why it matters:

- Counts become stale quickly and add review noise without helping contributors.

## Suggested GitHub Issue Split

Use these as separate issues so they can move cleanly across GitHub accounts:

1. Security: Add regression tests for route auth on documents, source updates, and personnel endpoints.
2. Security: Replace content-derived upload IDs with random record IDs.
3. Security hardening: Add extraction budgets for uploaded PDF/DOCX preview parsing.
4. Architecture: Define the auth model before hosted or multi-user deployment.
5. Docs: Fix README broken links and dead `make check` command.
6. Handoff: Adopt and document the cross-account GitHub handoff workflow.
7. CI: Add Python 3.12 test, ruff, and mypy workflow.
8. Dependencies: Add lockfile strategy and dependency update automation.
9. Tests: Replace CWD-relative seed-data paths in tests with repo-root fixtures.
10. Config: Complete `.env.example` storage-path guidance.
11. API cleanup: Pick one canonical document-update route family.
12. Demo: Keep `/demo/status` synchronized with the demo router.
13. Docs: Clarify vestigial SQLModel/database boundary and remove stale exact counts.

## Cross-Account GitHub Handoff

Simple path:

1. Commit this file in the source account.
2. In the destination account or fork, create issues from the sections above:

```powershell
gh issue create --repo OWNER/REPO --title "Security: add route-auth regression tests" --body-file FEEDBACK_SECURITY_PASS.md --label security
gh issue create --repo OWNER/REPO --title "CI: add Python test and quality workflow" --body-file FEEDBACK_SECURITY_PASS.md --label developer-experience
```

For a cleaner split, copy each section into its own temporary Markdown file and use `--body-file` for each issue. The GitHub CLI documents `gh issue create --body-file` for creating issues from files. Source: [GitHub CLI manual: gh issue create](https://cli.github.com/manual/gh_issue_create).

Heavier path:

- If the entire repository should move accounts, use GitHub repository transfer. GitHub documents repository transfers separately and notes permission and ownership considerations. Source: [GitHub Docs: Transferring a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository).

Recommended project addition:

- Add `.github/ISSUE_TEMPLATE/feedback.yml` later to standardize these handoffs. GitHub supports issue templates for collecting structured issue details. Source: [GitHub Docs: Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository).

## Validation Performed

- Reviewed route auth declarations across `app/api/routes`.
- Reviewed upload preview and storage paths at a high level.
- Reviewed project tooling files: `pyproject.toml`, `.github`, `.gitignore`, and tests that still use CWD-relative seed paths.
- Folded in read-only subagent findings from a security-focused route/storage review and a repo-improvement review.
- Ran a focused TestClient auth check under `LOCAL_API_KEY=expected-key`; current working tree returns `401` for the previously exposed routes without the header.

Full suite run after the handoff file was created and before the final documentation-only additions: `python -m pytest tests/ -q` passed with `518 passed`.
