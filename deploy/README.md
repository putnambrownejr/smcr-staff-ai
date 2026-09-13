# Public library pilot

The pilot is a separate application: `app.public_library.app:app`. It serves a fixed
snapshot of 12 official reference links, eight draft template scaffolds, and two
prompt packs. The website and MCP tools read the same catalog. No login is required,
as requested for this public-reference pilot. Anyone who can reach it can read all
22 items. It is not a shared version of the personal dashboard.

## Run locally

From the repository root, with Python 3.12+ and uv:

```sh
uv sync --frozen --extra dev --extra cloud
uv run --frozen --extra cloud python -m app.public_library
```

Open **http://127.0.0.1:8010**. Connect an MCP client to
**http://127.0.0.1:8010/mcp**. Use that exact host; `localhost` is a different origin.
Stop the foreground process with Ctrl+C.

For Docker:

```sh
docker compose -f docker-compose.public.yml up --build
```

The public image runs as UID 10001, has no volumes, and is configured read-only by
Compose. The local dashboard's normal Compose configuration now persists project
outputs under `/data/projects`. Existing outputs inside an old container's
`/app/projects` must be copied out before replacing that container; setting the new
path does not migrate them.

## What is published

The only MCP tools are:

- `smcr_search_library(query, category, limit, offset)` — IDs, summaries and source links.
- `smcr_get_library_item(item_id)` — full draft scaffold or metadata, provenance and warning.

HTTP reads: `/health`, `/api/catalog`, `/api/items/{item_id}`, `/api/connection`.
The portal is `/`; its static assets are `/assets/`. The remote transport is
stateless Streamable HTTP with JSON responses, using the official MCP Python SDK.
[SDK ASGI integration](https://py.sdk.modelcontextprotocol.io/run/asgi/)

`catalog.json` is an explicit publication snapshot. Runtime does not scan folders,
load `.env`, initialize local stores, import `app.main`, ingest sources, or call
an LLM. Full publication text and worked operational examples are not included.
Template reference names are inherited drafts, not validated policy. All items
have `verification_status=not_live_verified` and `last_verified_at=null`.
Content fingerprints normalize CRLF/LF so builds agree across platforms.

The two small prompt packs under `app/public_library/packs/` are purpose-written
for this pilot. Older broad packs contain unverified current-policy claims and
are deliberately not included. No existing skills or hooks were changed.

## Deploy to Google Cloud Run

**Not deployed yet.** First choose a Google Cloud project with billing enabled and
install/authenticate the [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install).
No custom domain is necessary: Cloud Run supplies an HTTPS URL and supports
Streamable HTTP MCP servers. [Cloud Run MCP hosting](https://docs.cloud.google.com/run/docs/host-mcp-servers)

Use a dedicated project for the pilot. Before running the steps below, ensure the
deploying account can enable APIs, create the image repository and runtime service
account, submit builds, and deploy Cloud Run. Cloud Build's configured build account
needs permission to write the image to Artifact Registry. The runtime account needs
no application access to project data. Do not grant it broad project roles.
[Service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)

These are PowerShell commands. Replace `YOUR_PROJECT_ID` with your actual project.
`us-central1` is the example region; choose another region if appropriate. These
steps create billable cloud resources; they have not been executed by this change.

```powershell
$pilotProject = 'YOUR_PROJECT_ID'
$pilotRegion = 'us-central1'
$pilotService = 'smcr-public-library'
$pilotAccount = "smcr-public-runtime@$pilotProject.iam.gserviceaccount.com"
$pilotImage = "$pilotRegion-docker.pkg.dev/$pilotProject/smcr-public/library:pilot"

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com --project $pilotProject
gcloud artifacts repositories create smcr-public --repository-format docker --location $pilotRegion --project $pilotProject
gcloud iam service-accounts create smcr-public-runtime --display-name 'SMCR public library runtime' --project $pilotProject

uv run --frozen --extra cloud python scripts/build_public_catalog.py --check
gcloud builds submit . --project $pilotProject --region $pilotRegion --ignore-file deploy/public-library.gcloudignore --config deploy/cloudbuild.public.yaml --substitutions "_IMAGE=$pilotImage"
```

Run the three resource-creation commands once; reuse existing resources on later
deployments. Stop on any failed command. The explicit `--ignore-file` is essential:
only the runtime allowlist is uploaded, independently of Git ignore settings.
[Build submission](https://docs.cloud.google.com/sdk/gcloud/reference/builds/submit),
[Artifact Registry](https://docs.cloud.google.com/sdk/gcloud/reference/artifacts/repositories/create),
[service accounts](https://docs.cloud.google.com/sdk/gcloud/reference/iam/service-accounts/create)

Create the service with IAM access still restricted. The first revision answers
health probes but rejects content requests until its actual HTTPS origin is set:

```powershell
gcloud run deploy $pilotService --image $pilotImage --region $pilotRegion --project $pilotProject --service-account $pilotAccount --port 8080 --min-instances 0 --max-instances 2 --memory 512Mi --cpu 1 --concurrency 40 --timeout 60 --no-allow-unauthenticated
$pilotUrl = gcloud run services describe $pilotService --region $pilotRegion --project $pilotProject --format 'value(status.url)'
gcloud run services update $pilotService --region $pilotRegion --project $pilotProject --update-env-vars "SMCR_PUBLIC_BASE_URL=$pilotUrl"
gcloud run services add-iam-policy-binding $pilotService --region $pilotRegion --project $pilotProject --member allUsers --role roles/run.invoker
```

The final command makes the public library accessible without Google credentials,
including to remote AI clients. Do not apply it to the local dashboard. If the
organization blocks public access, stop and resolve that policy with its owner.
Minimum instances zero and maximum instances two limit capacity, not total spend;
builds, storage and serving can incur charges.
[Deploy options](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy),
[environment updates](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update),
[public access binding](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/add-iam-policy-binding)

Visit `$pilotUrl`, check `/health`, and connect clients to `$pilotUrl/mcp`.
If the hostname changes, update `SMCR_PUBLIC_BASE_URL`; arbitrary Host/Origin headers
are rejected. Reverse proxies must preserve the configured host. Uvicorn access
logging is disabled, but the hosting platform can still record request URLs/IPs:
search only public topics. No claim of anonymous or zero-log hosting is made.

## Connect an AI

Use the portal's **Copy connection URL** button. Select no authentication when
the client asks; this pilot intentionally exposes public information only.

- **Claude:** add the HTTPS URL as a custom remote connector. Remote connectors
  are available across clients including mobile; configure on web first.
  [Claude setup](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)
- **ChatGPT:** follow the current custom MCP/plugin connection flow. Developer
  availability depends on account/workspace policy. Actual phone behavior still
  needs a pilot with the intended accounts; local protocol tests do not establish
  mobile availability. [OpenAI setup](https://developers.openai.com/plugins/deploy/connect-chatgpt)
- **Gemini Spark:** eligible US adult personal accounts can configure a custom
  MCP app on the web and then use it on mobile. Work/school accounts are excluded,
  and Keep Activity must be on. [Google setup](https://support.google.com/gemini/answer/17209137)
- **Any other AI:** use a compatible remote MCP client, or copy a prompt/template
  from the website into the chat. Copied content and connector results are processed
  under the chosen AI provider's terms.

Provider documentation checked September 12, 2026; confirm availability at rollout.
This does not certify doctrine currency or authorization for official detachment use.

## Maintain and validate

Edit the explicit allowlists in `scripts/build_public_catalog.py` only after
reviewing the proposed publication content. Review the generated diff before release:

```sh
uv run --extra cloud python scripts/build_public_catalog.py
uv run --extra cloud python scripts/build_public_catalog.py --check
uv run --extra cloud --extra dev pytest tests/public_library/ -q
uv run --extra cloud --extra dev pytest tests/public_library/ -m e2e -q
uv run --extra cloud --extra dev mypy app tests
uv run --extra cloud --extra dev ruff check .
```

Browser tests require `uv run playwright install chromium`. CI checks the snapshot,
protocol, web behavior, type/lint checks, and builds the public Docker image.
`deploy/public-library-evaluations.xml` provides manual client acceptance questions;
these are not claims that ChatGPT/Claude/Gemini account tests have been performed.

The repository provenance links reference `main`; publish the corresponding code
changes there before distributing those links. The hosted snapshot fingerprint is
the identifier for its actual content, not a claim that `main` is immutable.

## Design decision and next phase

Accepted September 12, 2026: isolate public capability behind a separate app and
image, reuse the existing template loader only at build time, and share one snapshot
between browser and MCP. The user selected public-by-link access. The alternative
of exposing all dashboard routes would also expose local administration and
caller-selected user records; it was rejected for this pilot.

Shared saved work is a later project: authenticated identities, detachment membership,
authorization on every store/export, transactional persistence and private file
storage are required before adding personal records. A shared API key is not that
boundary. See `app/core/auth.py`, `app/api/routes/user_profile.py` and
`app/api/routes/sharing.py` for the current local implementation.

DRAFT — Verify all references against current official sources before acting.
