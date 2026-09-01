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
KEY="agentic-memory-persist-$(date +%s)-$RANDOM"
LOG="${LOG:-/tmp/openai_interview_probe_persist.log}"
PORT="$PORT" scripts/dev.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 80); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_interview_probe_persist_health.json 2>/dev/null && READY=1 && break || true
  sleep 0.25
done
[ "${READY:-0}" = 1 ] || { cat "$LOG" >&2; exit 1; }
curl -fsS -X POST "http://127.0.0.1:$PORT/v1/eval/batch" \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d "{\"batch_id\":\"$KEY\",\"purpose\":\"Persist a Pydantic eval batch receipt through Memory instead of local SQL\",\"classification\":\"internal\",\"persist_to_memory\":true,\"items\":[{\"item_id\":\"memory-persist\",\"question\":\"What evidence supports using Memory ArangoDB and Qdrant for this control plane?\",\"classification\":\"internal\"}]}" \
  >/tmp/openai_interview_probe_persist_response.json
uv run --extra dev python - "$KEY" <<'PY'
import json, sys
from pathlib import Path
import httpx
key=sys.argv[1]
body=json.loads(Path('/tmp/openai_interview_probe_persist_response.json').read_text())
assert body['schema']=='openai_interview.eval_batch.v1'
assert body['receipt_refs'], body
client=httpx.Client(base_url='http://127.0.0.1:8601', timeout=httpx.Timeout(10.0, connect=2.0))
readback=client.post('/list', json={'collection':'openai_interview_receipts','filters':{'_key':key},'limit':1}).json()
assert readback['count']==1, readback
doc=readback['documents'][0]
assert doc['schema']=='openai_interview.eval_batch_receipt.v1'
assert doc['classification']=='internal'
receipt={'schema':'openai_interview.probe.memory_persist.v1','status':'PASS','key':key,'readback_count':readback['count'],'stored_schema':doc['schema']}
Path('receipts/agentic/live-memory-persist.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
