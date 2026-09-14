# Security Policy

`smcr-staff-ai` is for UNCLASSIFIED, public/open-source-ready prototyping only.

Do not submit, commit, ingest, or test with:

- Classified information
- CUI unless a future approved environment explicitly supports it
- Secrets, credentials, API keys, tokens, or private certificates
- PII beyond the minimum needed for a safe local prototype
- COMSEC, keying material, real frequencies, call signs, or sensitive network details
- Current operational movement details, real operational plans, or sensitive unit-specific information
- Private eligibility data or sensitive personnel/career counseling details for billet matching

Runtime guardrails detect common sensitive keywords and limit responses to generic training checklists. These checks are not complete and are not a substitute for user judgment, OPSEC review, or organizational policy.

When `LOCAL_API_KEY` is configured, `/dashboard` presents an unlock page until the user supplies the matching `X-Local-API-Key` header. The configured secret is never embedded in the returned HTML. The browser keeps the user-entered value in that tab's session storage and uses it for API requests; close the tab to end that browser session. With no configured key, the existing local no-key behavior remains. This is a shared installation passkey, not per-user authorization. See [dashboard access handling](app/api/routes/dashboard.py), [browser unlock](app/static/dashboard/access.js), and [API key validation](app/core/auth.py).

Private vulnerability reporting was enabled and verified on the source repository on 13 September 2026. Use the [private report form](https://github.com/putnambrownejr/smcr-staff-ai/security/advisories/new), with a minimal fictional reproduction. Do not post sensitive examples in public issues. Availability of this form does not promise a response time or ongoing maintenance.

Copies in another organization do not inherit the source repository's reporting settings. The receiving owner must enable private reporting or document its own private channel. If a private form is unavailable, ask that repository's owner for a channel without including vulnerability details. See [GitHub's private vulnerability reporting documentation](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
