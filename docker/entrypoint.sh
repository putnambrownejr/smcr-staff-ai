#!/bin/sh
set -eu

mkdir -p data/local_context
mkdir -p data/local_context/session_handoffs

python -m app.db.init_db

exec "$@"
