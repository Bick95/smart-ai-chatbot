#!/usr/bin/env bash
# Auth comes from .env (AUTH_PROVIDER defaults to postgres in settings).
# For mock auth without Postgres: AUTH_PROVIDER=mock ./run_dev_server.sh
# Only pass JWT_SECRET_KEY through if already set; otherwise let pydantic load from .env
[ -n "${JWT_SECRET_KEY:-}" ] && export JWT_SECRET_KEY

uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
