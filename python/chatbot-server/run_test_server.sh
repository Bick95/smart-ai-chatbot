#!/usr/bin/env bash
# Test mode: starts Postgres via Docker Compose, runs server with postgres auth, cleans up on exit.
# Usage: ./run_test_server.sh [--reset]
#   --reset  Wipe database volume on start and exit (docker compose down -v)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESET_DB=""
for arg in "$@"; do
  case "$arg" in
    --reset) RESET_DB=1 ;;
  esac
done

_cleaned=""
cleanup() {
  if [[ -n "$_cleaned" ]]; then return; fi
  _cleaned=1
  echo "Shutting down..."
  if [[ -n "$RESET_DB" ]]; then
    docker compose down -v
  else
    docker compose down
  fi
}

trap cleanup EXIT

if [[ -n "$RESET_DB" ]]; then
  echo "Resetting database (removing volumes)..."
  docker compose down -v 2>/dev/null || true
fi

# Ensure postgres data directory exists (matches docker-compose POSTGRES_DATA_PATH)
echo "Database storage location: ${POSTGRES_DATA_PATH:-./postgres_data}"
mkdir -p "${POSTGRES_DATA_PATH:-./postgres_data}"

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
# Only export JWT_SECRET_KEY if already set; otherwise app loads from .env
[[ -n "${JWT_SECRET_KEY}" ]] && export JWT_SECRET_KEY

uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
