#!/usr/bin/env bash
# Root CI entrypoint: run the same pipeline locally or from GitHub Actions.
#
# Pipeline shape (each service script does the real work):
#   1. Static checks only — lint, format check, typecheck (web), unit tests.
#   2. If you pass --build — Docker image build, then a short smoke test against the running container.
# This file only parses flags and invokes python/chatbot-server/ci.sh and/or web/chat-ui/ci.sh in order.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: ci.sh [--only SERVICE ...] [--build]

  Default: run CI for all services (python, web), in order.

  --only SERVICE [...]   Limit to one or more services (deduplicated, order preserved).
                         Aliases:
                           python | chatbot-server  →  python/chatbot-server
                           web | frontend           →  web/chat-ui

  --build                After tests: docker build + container smoke (health / HTTP 200).

  -h, --help             Show this help.

TODO: Enable mypy in python/chatbot-server/ci.sh when the codebase is ready.
EOF
}

BUILD=false
ONLY=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --build)
      BUILD=true
      shift
      ;;
    --only)
      shift
      while [[ $# -gt 0 && $1 != --* ]]; do
        ONLY+=("$1")
        shift
      done
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

canonical_service() {
  case "$1" in
    python | chatbot-server) echo python ;;
    web | frontend) echo web ;;
    *)
      echo "Unknown service: $1 (use python|chatbot-server|web|frontend)" >&2
      return 1
      ;;
  esac
}

# --- Resolve which services to run (default: python then web; dedupe --only aliases) ---

declare -A _ci_seen=()
SERVICES=()
if [[ ${#ONLY[@]} -eq 0 ]]; then
  SERVICES=(python web)
else
  for raw in "${ONLY[@]}"; do
    c="$(canonical_service "$raw")" || exit 1
    [[ -n ${_ci_seen[$c]+x} ]] && continue
    _ci_seen[$c]=1
    SERVICES+=("$c")
  done
fi

# Forward --build to child scripts so they know to continue past static checks into Docker + smoke.

extra=()
if [[ "$BUILD" == true ]]; then
  extra+=(--build)
fi

# --- Run each selected service in order (static checks always; build+smoke only with --build) ---

for svc in "${SERVICES[@]}"; do
  case "$svc" in
    python) "$ROOT/python/chatbot-server/ci.sh" "${extra[@]}" ;;
    web) "$ROOT/web/chat-ui/ci.sh" "${extra[@]}" ;;
  esac
done

echo "==> CI finished successfully."
