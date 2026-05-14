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

Report security issues privately to the maintainers once a public release process exists. Until then, do not post sensitive examples in public issues.
