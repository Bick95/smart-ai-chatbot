#!/usr/bin/env bash
# Test mode: starts a database via Docker Compose, runs server with SQL auth, cleans up on exit.
# Requires .env and/or .env.local (same layering as src/settings.py: .env then .env.local overrides).
# All database passwords must be set — this script does not supply default passwords.
# Usage: ./run_test_server.sh [--reset]
#   --reset  Wipe database volume on start and exit (docker compose down -v)
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]] && [[ ! -f .env.local ]]; then
  echo "Missing .env or .env.local in ${SCRIPT_DIR}. Copy .env.example and set secrets (passwords required)." >&2
  exit 1
fi
set -a
# shellcheck source=/dev/null
[[ -f .env ]] && source .env
# shellcheck source=/dev/null
[[ -f .env.local ]] && source .env.local
set +a

_required_password_vars=(
  APP_DATA_DATABASE_ADMIN_PASSWORD
  AUTHENTICATION_SERVICE_PASSWORD
  APP_DATA_DATABASE_PASSWORD
)
for var in "${_required_password_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Set ${var} to a non-empty value in .env or .env.local (no defaults in run_test_server.sh)." >&2
    exit 1
  fi
done

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

# Ensure data directory exists (matches docker-compose DATABASE_DATA_PATH)
echo "Database storage location: ${DATABASE_DATA_PATH:-./database_data}"
mkdir -p "${DATABASE_DATA_PATH:-./database_data}"

echo "Starting database..."
docker compose up -d

_pg_user="${APP_DATA_DATABASE_ADMIN_USERNAME:-chatbot}"
_pg_db="${APP_DATA_DATABASE_NAME:-chatbot}"

# Wait for the database to be ready
echo "Waiting for database..."
ready=0
for i in $(seq 1 30); do
  if docker compose exec -T database pg_isready -U "${_pg_user}" -d "${_pg_db}" 2>/dev/null; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != "1" ]]; then
  echo "Database failed to become ready within 30 seconds"
  exit 1
fi

# Only export JWT_SECRET_KEY if already set; otherwise app loads from .env / .env.local via Settings
[[ -n "${JWT_SECRET_KEY:-}" ]] && export JWT_SECRET_KEY

uv sync
uv run uvicorn src.server.app:app --reload --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
