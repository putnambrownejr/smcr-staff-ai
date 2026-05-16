# ChatGPT Repo Mode

This repository is structured so ChatGPT can understand and reason about the project directly from GitHub, even when it cannot access the user's local files, local storage, or running machine state.

## What Works Well From GitHub Alone

- API contract discovery through FastAPI routes and Pydantic schemas
- architectural reasoning through the modular service layout
- understanding intended workflows through README examples and seed manifests
- stateless demo use through the `/demo/*` routes
- draft generation workflows such as:
  - `/demo/analysis/summarize`
  - `/demo/staff-products/draft`
  - `/demo/agents/{agent_id}/run`
  - `/demo/chief/brief`
  - `/demo/career/watch`

## What Does Not Come From GitHub Alone

GitHub access does not provide:

- ignored local context under `data/local_context/`
- user-uploaded RQS, BIO, orders, receipts, or notes
- stored handoffs, drill plans, or tracked opportunities on the user's machine
- future email/calendar connector data
- runtime secrets, environment variables, or local API keys

That distinction matters. ChatGPT can understand the code and use demo workflows from the repo, but private user workflows still depend on a local or hosted runtime.

## Repo-Friendly Design Choices

- public-source manifests and markdown source notes are committed
- large PDFs and user-provided files stay local or are fetched from official sources
- local context does not mutate canonical doctrine or organizational structures
- request schemas include examples so OpenAPI is easier to interpret
- demo routes avoid prior setup and return deterministic advisory examples

## Recommended ChatGPT-Visible Entry Points

If ChatGPT only has the repo:

1. start with `README.md`
2. inspect `AGENTS.md`
3. inspect `docs/project_purpose.md`
4. inspect `docs/architecture.md`
5. inspect `docs/chatgpt_repo_mode.md`
6. search `app/services/agents/registry.py`
7. search `chatgpt_app/main.py` and `app/chatgpt_bridge/adapter.py`
8. read `app/main.py` and `app/api/routes/`
9. use `/demo/*` routes and `docs/examples/` as canonical examples of intended behavior

## Required Search Behavior

If ChatGPT is connected to this repo and the user asks what the system can do, which tool to use, or how to solve a workflow inside the repo, it should search the repo first instead of relying on generic memory.

Minimum search targets:

- `app/services/agents/`
- `app/services/agents/registry.py`
- `chatgpt_app/main.py`
- `app/chatgpt_bridge/adapter.py`
- `app/api/routes/`
- `docs/examples/`

Typical search patterns:

```powershell
rg -n "build_staff_package|frago|conop|aar|agent|tool|route" C:\smcr-staff-ai
rg -n "class .*Agent|def build_.*agent" C:\smcr-staff-ai\app\services\agents
rg -n "@router|APIRouter" C:\smcr-staff-ai\app\api\routes
```

## Path To A Fuller ChatGPT Integration

The repo is now friendlier to ChatGPT-as-reader. To make it friendlier to ChatGPT-as-product, the next steps would be:

1. refine OpenAPI metadata and tool descriptions further
2. preserve stateless demo workflows as the public contract
3. expose the most valuable routes through a ChatGPT app or plugin surface
4. keep private/local context behind explicit local or hosted runtime boundaries
