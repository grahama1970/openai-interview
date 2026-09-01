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
OUT="${OUT:-/tmp/openai-interview-hack-probe}"
LOG="${LOG:-/tmp/openai_interview_probe_hack.log}"
rm -rf "$OUT"
OPENAI_INTERVIEW_ENABLE_HACK_VERIFY=true PORT="$PORT" scripts/dev.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 80); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_interview_probe_hack_health.json 2>/dev/null && READY=1 && break || true
  sleep 0.25
done
[ "${READY:-0}" = 1 ] || { cat "$LOG" >&2; exit 1; }
curl -fsS -X POST "http://127.0.0.1:$PORT/v1/hack/verify" \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d "{\"artifact_root\":\"$OUT\",\"classification\":\"internal\"}" \
  >/tmp/openai_interview_probe_hack_response.json
python3 - <<'PY'
import json
from pathlib import Path
body=json.loads(Path('/tmp/openai_interview_probe_hack_response.json').read_text())
assert body['schema']=='openai_interview.hack_verify.v1'
assert body['status']=='pass'
receipt=json.loads(Path(body['receipt']).read_text())
assert receipt['schema']=='hack.verify_receipt.v1'
assert receipt['status']=='PASS'
print(json.dumps({'schema':'openai_interview.probe.hack.v1','status':'PASS','receipt':body['receipt'],'steps':len(receipt['steps'])}))
PY
