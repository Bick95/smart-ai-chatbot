#!/usr/bin/env bash
# chat-ui: npm lint → typecheck → tests → optional Docker build + HTTP smoke.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

BUILD=false
for arg in "$@"; do
  if [[ "$arg" == "--build" ]]; then
    BUILD=true
  fi
done

echo "==> [web] npm ci"
npm ci

echo "==> [web] lint"
npm run lint

echo "==> [web] typecheck"
npm run typecheck

echo "==> [web] tests (vitest run)"
npm run test:run

if [[ "$BUILD" != true ]]; then
  exit 0
fi

IMAGE_TAG="${SMART_AI_CHATBOT_WEB_IMAGE:-smart-ai-chatbot-chat-ui:ci}"

echo "==> [web] docker build ($IMAGE_TAG)"
docker build -t "$IMAGE_TAG" .

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
