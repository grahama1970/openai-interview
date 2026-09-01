#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p receipts/agentic
if [ -z "${PORT:-}" ]; then
  PORT="$(uv run --extra dev python - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    print(s.getsockname()[1])
PY
)"
fi
if [ -z "${WEB_PORT:-}" ]; then
  WEB_PORT="$(uv run --extra dev python - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    print(s.getsockname()[1])
PY
)"
fi
LOG="${LOG:-/tmp/openai_interview_probe_hot_reload.log}"
PORT="$PORT" WEB_PORT="$WEB_PORT" scripts/dev-all.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 120); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_interview_probe_hot_api.json 2>/dev/null && API_READY=1 || true
  curl -fsS "http://127.0.0.1:$WEB_PORT" >/tmp/openai_interview_probe_hot_web.html 2>/dev/null && WEB_READY=1 || true
  [ "${API_READY:-0}" = 1 ] && [ "${WEB_READY:-0}" = 1 ] && break
  sleep 0.25
done
[ "${API_READY:-0}" = 1 ] && [ "${WEB_READY:-0}" = 1 ] || { cat "$LOG" >&2; exit 1; }
grep -E 'StatReload|Started reloader process' "$LOG" >/tmp/openai_interview_probe_hot_api_log.txt
grep -E 'VITE|ready in|Local:' "$LOG" >/tmp/openai_interview_probe_hot_vite_log.txt
uv run --extra dev python - <<'PY'
import json
from pathlib import Path
health=json.loads(Path('/tmp/openai_interview_probe_hot_api.json').read_text())
html=Path('/tmp/openai_interview_probe_hot_web.html').read_text()
assert health['schema']=='openai_interview.health.v1'
assert '<script' in html or '<div id="root"' in html
receipt={'schema':'openai_interview.probe.hot_reload.v1','status':'PASS','api_schema':health['schema'],'web_bytes':len(html)}
Path('receipts/agentic/hot-reload.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
