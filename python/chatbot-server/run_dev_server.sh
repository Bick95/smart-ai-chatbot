#!/usr/bin/env bash
# Dev mode: uses mock auth adapter (no Postgres required)
export AUTH_PROVIDER="${AUTH_PROVIDER:-mock}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY}"

uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
