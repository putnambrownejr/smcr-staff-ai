# Release snapshot handoff

This distribution is a versioned source snapshot, provided under the [MIT license](LICENSE), with no commitment to feature updates, response times, or ongoing support. A receiving organization may maintain its own copy. Copying this repository does not establish organizational approval or transfer GitHub security settings.

## Install and identify your copy

Follow [QUICKSTART.md](QUICKSTART.md). Retain the release tag or commit ID and its verification record when transferring a copy. Use the committed `uv.lock`; the startup scripts install with `uv sync --frozen`. First installation needs Python 3.12+, uv, and access to package downloads; the source ZIP is not an offline installer. Source: [start.bat](start.bat), [start.sh](start.sh).

Windows is the primary local acceptance target. CI exercises Windows and Linux. macOS and independent, uncoached user installation remain unverified until a recipient records a successful trial. Container build checks do not certify a hosted deployment. The optional public library has its own [deployment instructions](deploy/README.md); deploying it is not required to use the local dashboard.

## Capability boundary

The 37 listed local agents principally provide templates, checklists, and structured workflow outputs. Eight older agent IDs remain compatibility aliases after consolidation. Scenario inference is optional and requires the application's operation-specific payload approval. Public feeds require network access and may be unavailable or stale. Email and calendar providers are stubs; a consent plan is not a working connector. Outputs require human review and current-source verification. Sources: [agent registry](app/services/agents/registry.py), [external processing](app/services/external_processing/preflight.py), [data governance](docs/data_governance.md), [email providers](app/services/email/providers.py).

Saved automations hold standing instructions and build packets; they do not schedule or execute analysis. Roundtable packets can be handed to your own assistant; optional external perspectives use the application's approval path. MARADMIN and ALMAR have live feed adapters; NAVADMIN/ALNAV are portal links. Sources: [automations](app/api/routes/automations.py), [roundtable](app/services/agents/roundtable.py), [message watch](app/api/routes/message_watch.py).

## Preserve your work

Stop the dashboard before backing up or restoring. Preserve both the local state and project files, plus any custom module packs:

- Windows default state: `%LOCALAPPDATA%\smcr-staff-ai`.
- Linux/macOS default state: `$XDG_DATA_HOME/smcr-staff-ai`, or `~/.local/share/smcr-staff-ai` when unset.
- Project files: `projects/` beside the source code.
- `SMCR_STAFF_AI_HOME`, `PROJECTS_DIR`, or per-domain settings can override these locations. Preserve your local configuration privately; do not include credentials in a shared backup or repository.
- Docker Compose stores state and projects in the `smcr-data` named volume and mounts `modules/` from the host. Preserve that volume separately from the source tree.

Copy these directories to a private backup location. To restore, stop the application, preserve the current directories as a rollback copy, restore the saved directories to their original configured locations, then start the same application version. Confirm a profile, saved draft, and handoff are present before resuming work. Do not overwrite a newer installation's state without retaining a rollback copy. Sources: [storage configuration](app/core/config.py), [Compose configuration](docker-compose.yml).

## Receiving-user acceptance

One person other than the author should perform this trial on another machine without coaching, using fictional UNCLASSIFIED data. Record the date, OS, release tag/commit, result, and any instruction that needed clarification:

1. Follow the Quickstart from a clean source copy and open the dashboard.
2. Save a fictional profile and a drill handoff; reload and verify both.
3. Create an AAR draft, edit it, save it to a project, and open the Markdown and Word copies.
4. Shut down and restart. Verify the profile, handoff, and saved products remain.
5. If enabling a local passkey, confirm an unauthenticated browser is challenged and the correct passkey opens the dashboard.
6. Back up and restore fictional state using the procedure above; verify the saved work.

The receiving owner records acceptance and confirms its publication process before organizational distribution. The source owner handles transfer to FHG. No FHG URL, access credential, or approval is embedded in this repository. See [SECURITY.md](SECURITY.md) for private reporting; the receiving copy needs its own reporting arrangements.

DRAFT — Verify all references against current official sources before acting.
