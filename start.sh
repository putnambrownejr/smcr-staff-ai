#!/usr/bin/env bash
# smcr-staff-ai — one-command start for macOS / Linux
# Requires: Python 3.12+ and uv  (https://docs.astral.sh/uv/getting-started/installation/)

set -euo pipefail
cd "$(dirname "$0")"

SMCR_PORT="${SMCR_PORT:-8000}"

if ! command -v uv &>/dev/null; then
  echo "uv not found. Install it from https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

echo "Installing / syncing dependencies..."
uv sync --frozen

if ! uv run python -m app.startup_preflight --port "$SMCR_PORT"; then
  exit 1
fi

echo ""
echo "Starting smcr-staff-ai at http://localhost:${SMCR_PORT}"
echo "Press Ctrl+C to stop."
echo ""

exec uv run uvicorn app.main:app --host 127.0.0.1 --port "$SMCR_PORT" --reload
