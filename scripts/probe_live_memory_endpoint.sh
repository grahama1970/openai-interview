#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [ -z "${PORT:-}" ]; then
  PORT="$(uv run --extra dev python - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    print(s.getsockname()[1])
PY
)"
fi
LOG="${LOG:-/tmp/openai_interview_probe_memory.log}"
PORT="$PORT" scripts/dev.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 80); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_interview_probe_memory_health.json 2>/dev/null && READY=1 && break || true
  sleep 0.25
done
[ "${READY:-0}" = 1 ] || { cat "$LOG" >&2; exit 1; }
curl -fsS -X POST "http://127.0.0.1:$PORT/v1/memory/recall" \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d '{"q":"What evidence supports using Memory ArangoDB and Qdrant for this control plane?","scope":"openai-interview","collections":["lessons"],"tags":["openai-interview","cyber-safety"],"k":3,"classification":"internal"}' \
  >/tmp/openai_interview_probe_memory_response.json
python3 - <<'PY'
import json
from pathlib import Path
body=json.loads(Path('/tmp/openai_interview_probe_memory_response.json').read_text())
assert body['schema']=='openai_interview.memory_recall.v1'
assert body['status'] in {'pass','blocked'}
assert isinstance(body['item_count'], int)
assert body['classification']=='internal'
print(json.dumps({'schema':'openai_interview.probe.memory.v1','status':'PASS','memory_status':body['status'],'item_count':body['item_count']}))
PY
