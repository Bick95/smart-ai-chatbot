#!/usr/bin/env bash
# Orchestrate full-stack Docker Compose: Postgres + FastAPI + nginx (web).
# Prereq: Docker with Compose v2. From repo root: ./deploy-compose.sh up
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
    cat <<'EOF'
Usage: deploy-compose.sh <command>

  up       Build images (if needed) and start all services in the background.
  down     Stop and remove containers (keeps postgres_data volume).
  logs     Follow logs from all services (Ctrl+C to stop).
  ps       Show container status.
  build    Build images without starting.
  restart  Restart all running services.

Environment: create .env in the repo root (see compose.env.example).
  Required: OPENAI_API_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD, DATABASE_APP_PASSWORD

After `up` (defaults): web UI http://localhost:8080 , API http://localhost:8000 (override with WEB_PORT / API_PORT in .env).
EOF
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

if [[ ! -f .env ]]; then
    echo "Missing .env in repo root." >&2
    echo "Copy compose.env.example to .env and set OPENAI_API_KEY and JWT_SECRET_KEY." >&2
    exit 1
fi

cmd="$1"
shift

case "$cmd" in
    up)
        docker compose -f "$ROOT/docker-compose.yml" up -d --build "$@"
        echo ""
        echo "Stack is up. Web UI: http://localhost:8080 (set WEB_PORT in .env to change the host port)"
        echo "API (direct): http://localhost:8000 (set API_PORT in .env to change)"
        ;;
    down)
        docker compose -f "$ROOT/docker-compose.yml" down "$@"
        ;;
    logs)
        docker compose -f "$ROOT/docker-compose.yml" logs -f "$@"
        ;;
    ps)
        docker compose -f "$ROOT/docker-compose.yml" ps "$@"
        ;;
    build)
        docker compose -f "$ROOT/docker-compose.yml" build "$@"
        ;;
    restart)
        docker compose -f "$ROOT/docker-compose.yml" restart "$@"
        ;;
    -h | --help | help)
        usage
        exit 0
        ;;
    *)
        echo "Unknown command: $cmd" >&2
        usage >&2
        exit 1
        ;;
esac
