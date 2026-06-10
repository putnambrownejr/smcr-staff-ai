# Dashboard Startup Blocker

Date: 2026-06-04

## Objective

Capture the blocker encountered while trying to launch and open the local dashboard so the next pass can fix it without repeating setup work.

## BLUF

The app dependencies installed successfully, but the dashboard did not come up because the runtime storage path is only partially configurable through `.env`.

Some app paths correctly read from `Settings`, while other services still call `default_local_context_dir()` or related helpers directly. Those direct calls resolve to `%LOCALAPPDATA%\smcr-staff-ai` unless `SMCR_STAFF_AI_HOME` is set in the process environment.

In this workspace, writes outside the repo are restricted, so the app fails during startup before the dashboard becomes reachable.

## What Was Attempted

### 1. Verified the app was not already running

- `http://127.0.0.1:8000/health` was not reachable.
- No working `uvicorn` process was serving the app.

### 2. Installed local Python dependencies

Succeeded:

- created `.venv`
- ran editable install with `.[dev]`

This part worked and is not the blocker.

### 3. Tried standard local init and startup

Attempted:

- copy `.env.example` to `.env`
- run `python -m app.db.init_db`
- run `uvicorn app.main:app --reload`

Observed failure:

- SQLite could not open the database path
- default runtime paths were resolving outside the writable workspace

### 4. Redirected runtime paths into the repo workspace

Adjusted `.env` so these point into `data/local_runtime`:

- `DATABASE_URL`
- `LOCAL_CONTEXT_STORAGE_DIR`
- `SESSION_HANDOFF_STORAGE_DIR`
- `PRODUCT_TEMPLATE_STORAGE_DIR`
- `TRAVEL_CASE_STORAGE_DIR`
- `READING_CATALOG_STORAGE_DIR`
- `MARADMIN_FEED_STORAGE_DIR`
- `NAVY_MESSAGE_STORAGE_DIR`
- `DOD_WATCH_STORAGE_DIR`
- `CUSTOM_WATCH_FEED_STORAGE_DIR`

This was enough for DB init to proceed further, but not enough for full app startup.

### 5. Re-ran startup and captured the next failure

Observed startup error:

`PermissionError: [WinError 5] Access is denied: 'C:\\Users\\PutnamBrowne\\AppData\\Local\\smcr-staff-ai'`

The trace showed startup was still trying to create:

- `local_context/document_updates`

under the default `%LOCALAPPDATA%` root.

## Root Cause Read

The configuration model is inconsistent.

There appear to be two patterns in the codebase:

### Pattern A: Good / configurable

Routes and services that use `get_settings()` and read configured storage dirs from:

- `app/core/config.py`
- `.env`

These are compatible with repo-local overrides.

### Pattern B: Problematic / direct default-path coupling

Some services import and call helpers like:

- `default_local_context_dir()`
- `default_session_handoff_dir()`

directly, instead of flowing all paths through `Settings`.

Examples seen during inspection:

- `app/services/ingestion/document_update_store.py`
- `app/services/actions/tracker.py`
- `app/services/opportunities/tracker.py`
- `app/services/calendar/plan_store.py`
- `app/services/ingestion/source_state_store.py`
- `app/services/staff/battle_rhythm_store.py`

Those direct calls still depend on:

- `SMCR_STAFF_AI_HOME`, or
- unrestricted access to `%LOCALAPPDATA%`

## Why I Stopped

Per instruction, I did not keep forcing it once the failure pattern was clear.

At that point, the problem was no longer "start the app." It was:

- either patch configuration consistency across the app, or
- ensure the process environment always sets `SMCR_STAFF_AI_HOME`

That is a real fix path, not a quick link/open issue.

## Safest Next Fix Options

### Option 1. Best long-term fix

Normalize all local storage paths through `Settings`.

Meaning:

- stop direct calls to `default_local_context_dir()` in runtime services where configurable paths already exist
- pass storage roots from route dependencies or constructors consistently

Why this is best:

- cleaner architecture
- easier testing
- fewer environment-specific surprises
- `.env` overrides actually become authoritative

### Option 2. Quick operational fix

Make local launch scripts explicitly set:

- `SMCR_STAFF_AI_HOME=<repo-local-runtime-path>`

before starting the app.

Why this works:

- minimal code change
- likely enough to get the dashboard up quickly

Tradeoff:

- still leaves split configuration behavior in the codebase

## Suggested Next Debug Sequence

1. Search for all direct uses of:
   - `default_local_context_dir`
   - `default_session_handoff_dir`
   - `default_*_dir`
2. Decide whether those should:
   - take an injected path, or
   - continue using environment-rooted defaults intentionally
3. If you want the app to be workspace-runnable by default, standardize on `Settings`.
4. After path normalization:
   - rerun `python -m app.db.init_db`
   - rerun `uvicorn app.main:app --reload`
   - verify `/health`
   - then open `/dashboard`

## Commands / Outputs Worth Remembering

Dependency install succeeded.

Foreground launch with repo-local `.env` overrides still failed with:

- `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\PutnamBrowne\\AppData\\Local\\smcr-staff-ai'`

The failure occurred during app import/startup, before the HTTP server was available.

## Recommendation

Treat this as a configuration-consistency cleanup task, not a dashboard bug.

The dashboard may be fine. The app is failing before the dashboard gets a chance to exist.
