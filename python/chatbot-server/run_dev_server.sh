#!/usr/bin/env bash
uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
