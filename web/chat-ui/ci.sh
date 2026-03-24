#!/usr/bin/env bash
# chat-ui CI: static checks, then (optional) Docker build + smoke on GET /.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

BUILD=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    BUILD=true
  fi
done

# =============================================================================
# Phase 1 — Static checks (host-only; no Docker image built or run in this block)
#   - Install deps, ESLint, TypeScript compile check, Vitest unit run.
# =============================================================================

echo "==> [web] npm ci"
npm ci

echo "==> [web] lint"
npm run lint

echo "==> [web] typecheck"
npm run typecheck

echo "==> [web] tests (vitest run)"
npm run test:run

# Without --build we stop after Phase 1.

if [[ "$BUILD" != true ]]; then
  exit 0
fi

# =============================================================================
# Phase 2 — Container image build (static site + nginx from Dockerfile)
# =============================================================================

IMAGE_TAG="${SMART_AI_CHATBOT_WEB_IMAGE:-smart-ai-chatbot-chat-ui:ci}"

echo "==> [web] docker build ($IMAGE_TAG)"
docker build -t "$IMAGE_TAG" .

# =============================================================================
# Phase 3 — Smoke test (run container, poll until GET / returns 200 or timeout)
# =============================================================================

echo "==> [web] docker smoke: GET /"
cid="$(docker run -d --rm -p 0:80 "$IMAGE_TAG")"

cleanup() {
  docker stop "$cid" >/dev/null 2>&1 || true
}
trap cleanup EXIT

port="$(docker port "$cid" 80 | head -1 | sed 's/.*://')"
ok=false
for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${port}/" >/dev/null 2>&1; then
    ok=true
    break
  fi
  sleep 1
done

if [[ "$ok" != true ]]; then
  echo "Smoke failed: / did not respond on port ${port}" >&2
  exit 1
fi

echo "Smoke OK (http://127.0.0.1:${port}/)"
trap - EXIT
cleanup
