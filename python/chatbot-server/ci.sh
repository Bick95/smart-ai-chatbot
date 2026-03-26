#!/usr/bin/env bash
# chatbot-server CI: static checks, then (optional) Docker build + smoke on /health.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# TODO: Add `uv run mypy src` (and dev dependency) once type checking is ready for CI.

BUILD=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    BUILD=true
  fi
done

# =============================================================================
# Phase 1 — Static checks (host-only; no Docker image built or run in this block)
#   - Lint + format gate, then unit tests (integration-marked tests skipped).
# =============================================================================

echo "==> [python] ruff check"
uv run ruff check src tests

echo "==> [python] ruff format --check"
uv run ruff format --check src tests

echo "==> [python] pytest (exclude integration marker)"
uv run pytest -m "not integration"

# Without --build we stop after Phase 1.

if [[ "$BUILD" != true ]]; then
  exit 0
fi

# =============================================================================
# Phase 2 — Container image build (production-like artifact from Dockerfile)
# =============================================================================

IMAGE_TAG="${SMART_AI_CHATBOT_IMAGE:-smart-ai-chatbot-chatbot-server:ci}"

echo "==> [python] docker build ($IMAGE_TAG)"
docker build -t "$IMAGE_TAG" .

# =============================================================================
# Phase 3 — Smoke test (run container, poll until GET /health succeeds or timeout)
# =============================================================================

echo "==> [python] docker smoke: GET /health"
cid="$(docker run -d --rm -p 0:8000 \
  -e OPENAI_API_KEY=sk-ci-smoke-dummy-key-for-docker-health \
  -e AUTHENTICATION_SERVICE_PROVIDER=mock \
  -e APP_DATA_DATABASE_PROVIDER=mock \
  -e JWT_SECRET_KEY=ci-smoke-jwt-secret-min-32-chars-ok \
  "$IMAGE_TAG")"

cleanup() {
  docker stop "$cid" >/dev/null 2>&1 || true
}
trap cleanup EXIT

port="$(docker port "$cid" 8000 | head -1 | sed 's/.*://')"
ok=false
for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
    ok=true
    break
  fi
  sleep 1
done

if [[ "$ok" != true ]]; then
  echo "Smoke failed: /health did not respond on port ${port}" >&2
  exit 1
fi

echo "Smoke OK (http://127.0.0.1:${port}/health)"
trap - EXIT
cleanup
