#!/usr/bin/env bash
# Test mode: starts Postgres via Docker Compose, runs server with postgres auth, cleans up on exit.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

_cleaned=""
cleanup() {
  if [[ -n "$_cleaned" ]]; then return; fi
  _cleaned=1
  echo "Shutting down..."
  docker compose down
}

trap cleanup EXIT

echo "Starting Postgres..."
docker compose up -d

# Wait for Postgres to be ready
echo "Waiting for Postgres..."
ready=0
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U chatbot -d chatbot 2>/dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != "1" ]]; then
  echo "Postgres failed to become ready within 30 seconds"
  exit 1
fi

export AUTH_PROVIDER=postgres
export DATABASE_URL="postgresql://chatbot:chatbot@localhost:5432/chatbot"
export JWT_SECRET_KEY="${JWT_SECRET_KEY}"

uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
