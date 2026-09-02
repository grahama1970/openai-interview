#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p receipts/agentic
IMAGE="openai-interview-control-plane:local"
CID=""
PORT="$(python3 - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()
PY
)"
cleanup() {
  if [[ -n "$CID" ]]; then docker rm -f "$CID" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

docker build -t "$IMAGE" . >/tmp/openai_interview_docker_build.log
USER_READBACK="$(docker image inspect "$IMAGE" --format '{{.Config.User}}')"
CID="$(docker run --rm -d -p "127.0.0.1:${PORT}:8080" -e OPENAI_INTERVIEW_API_KEY=dev-key "$IMAGE")"
for _ in $(seq 1 30); do
  if python3 - "$PORT" <<'PY' >/tmp/openai_interview_docker_health.json 2>/dev/null
import json, sys, urllib.request
port=sys.argv[1]
with urllib.request.urlopen(f'http://127.0.0.1:{port}/health/live', timeout=1) as r:
    body=json.loads(r.read().decode())
assert body['schema'] == 'openai_interview.health.v1'
assert body['status'] == 'ok'
print(json.dumps(body))
PY
  then
    break
  fi
  sleep 1
done
python3 - "$USER_READBACK" "$PORT" <<'PY'
import json, sys
from pathlib import Path
health=json.loads(Path('/tmp/openai_interview_docker_health.json').read_text())
receipt={
  'schema':'openai_interview.probe.docker.v1',
  'status':'PASS',
  'image':'openai-interview-control-plane:local',
  'container_user':sys.argv[1],
  'port':int(sys.argv[2]),
  'health':health,
}
assert receipt['container_user'] == 'appuser'
Path('receipts/agentic/docker-check.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
