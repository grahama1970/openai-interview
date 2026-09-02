#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p receipts/agentic
PORT="${PORT:-$(uv run --extra dev python - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1', 0))
    print(s.getsockname()[1])
PY
)}"
LOG="${LOG:-/tmp/openai_interview_probe_star_wars_brave.log}"
PORT="$PORT" scripts/dev.sh >"$LOG" 2>&1 &
PID=$!
cleanup() { pkill -P "$PID" 2>/dev/null || true; kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
for _ in $(seq 1 120); do
  curl -fsS "http://127.0.0.1:$PORT/health/live" >/tmp/openai_star_wars_health.json 2>/dev/null && break
  sleep 0.25
done
curl -fsS -H 'x-api-key: dev-key' "http://127.0.0.1:$PORT/v1/brave-search/star-wars/obscure-characters" > /tmp/openai_star_wars_response.json
uv run --extra dev python - <<'PY'
import json
from pathlib import Path
body = json.loads(Path('/tmp/openai_star_wars_response.json').read_text())
if body.get('schema') != 'openai_interview.star_wars_obscure_characters.v1':
    raise SystemExit('wrong schema')
characters = body.get('characters', [])
if len(characters) != 30:
    raise SystemExit(f'expected 30 characters, got {len(characters)}')
for row in characters:
    if set(row) != {'level', 'name', 'origin', 'bio'}:
        raise SystemExit(f'unexpected character fields: {row}')
    if not isinstance(row['level'], int) or not 1 <= row['level'] <= 5:
        raise SystemExit(f'invalid level: {row}')
    if not row['name'] or not row['origin'] or len(row['bio']) < 40:
        raise SystemExit(f'invalid row: {row}')
receipt = {
    'schema': 'openai_interview.probe.star_wars_brave.v1',
    'status': 'PASS',
    'source': body['source'],
    'source_count': body['source_count'],
    'character_count': len(characters),
    'first_character': characters[0]['name'],
}
Path('receipts/agentic/star-wars-brave.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
