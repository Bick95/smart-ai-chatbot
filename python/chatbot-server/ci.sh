#!/usr/bin/env bash
# chatbot-server: ruff → tests → optional Docker build + /health smoke.
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

echo "==> [python] ruff check"
uv run ruff check src tests

echo "==> [python] ruff format --check"
uv run ruff format --check src tests

echo "==> [python] pytest (exclude integration marker)"
uv run pytest -m "not integration"

if [[ "$BUILD" != true ]]; then
  exit 0
fi

IMAGE_TAG="${SMART_AI_CHATBOT_IMAGE:-smart-ai-chatbot-chatbot-server:ci}"

echo "==> [python] docker build ($IMAGE_TAG)"
docker build -t "$IMAGE_TAG" .

echo "==> [python] docker smoke: GET /health"
cid="$(docker run -d --rm -p 0:8000 \
  -e OPENAI_API_KEY=sk-ci-smoke-dummy-key-for-docker-health \
  -e AUTH_PROVIDER=mock \
  -e APP_DATA_PROVIDER=mock \
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
