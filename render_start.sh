#!/usr/bin/env bash
set -euo pipefail

# Run DB migrations
alembic upgrade head

# Start API server
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
