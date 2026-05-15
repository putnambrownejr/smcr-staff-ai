# Local Docker Use

This repo can run locally in Docker without touching the Swagger page for setup work.

The Docker path is best for:

- keeping the app off your main Python environment
- running the backend in one repeatable command
- preparing for a future Raspberry Pi or small-box deployment

## Quick Start

From `C:\smcr-staff-ai`:

```powershell
docker compose up --build
```

Then open:

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Dashboard: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

## What The Container Does

On startup the container:

1. ensures local storage directories exist
2. initializes the local SQLite database
3. starts the FastAPI app on port `8000`

## Local Storage Behavior

By default, Docker uses a named volume for:

- `/app/data/local_context`

That means your personal data survives container restarts without forcing you to expose it elsewhere.

## Default Local-Docker Settings

The compose file defaults to:

- `DATABASE_URL=sqlite:///./data/local_context/smcr_staff_ai.db`
- `ENVIRONMENT=local-docker`
- `PUBLIC_SOURCE_ONLY=true`

You can override these with a local `.env` file if you want.

## Useful Commands

```powershell
make docker-build
make docker-up
make docker-logs
make docker-down
```

Or plain Docker Compose:

```powershell
docker compose up --build -d
docker compose logs -f api
docker compose down
```

## Optional Postgres

For normal personal use, the local SQLite path is enough.

If you want to exercise the Postgres container too:

```powershell
docker compose --profile postgres up --build
```

That gives you a local Postgres service as a development option, but it is not required for ordinary use.

## Why This Is The Right Near-Term Shape

This keeps the system:

- local
- cheap
- easy to restart
- closer to a future Raspberry Pi deployment

without forcing you into cloud hosting or a more complicated tool bridge yet.
