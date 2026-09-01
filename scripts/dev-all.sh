#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PORT="${PORT:-8080}"
export API_PORT="$PORT"
export WEB_PORT="${WEB_PORT:-5173}"
scripts/dev.sh &
API_PID=$!
trap 'kill $API_PID ${WEB_PID:-} 2>/dev/null || true; wait $API_PID ${WEB_PID:-} 2>/dev/null || true' EXIT
(cd web && npm install --silent && npm run dev) &
WEB_PID=$!
wait -n "$API_PID" "$WEB_PID"
