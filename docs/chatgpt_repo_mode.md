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
2. inspect `docs/architecture.md`
3. inspect `docs/chatgpt_repo_mode.md`
4. read `app/main.py` and `app/api/routes/`
5. use `/demo/*` routes as canonical examples of intended behavior

## Path To A Fuller ChatGPT Integration

The repo is now friendlier to ChatGPT-as-reader. To make it friendlier to ChatGPT-as-product, the next steps would be:

1. refine OpenAPI metadata and tool descriptions further
2. preserve stateless demo workflows as the public contract
3. expose the most valuable routes through a ChatGPT app or plugin surface
4. keep private/local context behind explicit local or hosted runtime boundaries
