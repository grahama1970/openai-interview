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
LOG="${LOG:-/tmp/openai_interview_probe_hack_audit.log}"
OPENAI_INTERVIEW_ENABLE_HACK_AUDIT=true PORT="$PORT" scripts/dev.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 80); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_interview_probe_hack_audit_health.json 2>/dev/null && READY=1 && break || true
  sleep 0.25
done
[ "${READY:-0}" = 1 ] || { cat "$LOG" >&2; exit 1; }
curl -fsS -X POST "http://127.0.0.1:$PORT/v1/hack/audit" \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d '{"target_kind":"demo_vulnerable_python","tool":"bandit","severity":"low","persist_to_memory":true,"classification":"internal"}' \
  >/tmp/openai_interview_probe_hack_audit_response.json
uv run --extra dev python - <<'PY'
import json
from pathlib import Path
import httpx
body=json.loads(Path('/tmp/openai_interview_probe_hack_audit_response.json').read_text())
assert body['schema']=='openai_interview.hack_audit.v1', body
assert body['status']=='pass', body
assert body['finding_count'] >= 1, body
assert body['high_count'] >= 1, body
assert 'CWE-78' in body['cwes'], body
assert body['receipt_ref'], body
key=body['receipt_ref'].split('/')[-1]
client=httpx.Client(base_url='http://127.0.0.1:8601', timeout=httpx.Timeout(10.0, connect=2.0))
readback=client.post('/list', json={'collection':'openai_interview_hack_scans','filters':{'_key':key},'limit':1}).json()
assert readback['count']==1, readback
doc=readback['documents'][0]
assert doc['schema']=='hack.audit_memory_summary.v1'
assert doc['finding_count'] >= 1
assert 'CWE-78' in doc['cwes']
receipt={'schema':'openai_interview.probe.hack_audit.v1','status':'PASS','finding_count':body['finding_count'],'high_count':body['high_count'],'cwes':body['cwes'],'memory_ref':body['receipt_ref'],'readback_count':readback['count']}
Path('receipts/agentic/hack-audit-endpoint.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
