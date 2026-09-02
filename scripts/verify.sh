#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p receipts
uv run --extra dev python -m compileall -q src tests scripts
uv run --extra dev pytest --cov=openai_interview --cov-report=json:receipts/coverage.json
uv run --extra dev python scripts/check_contracts.py
uv run --extra dev python scripts/check_immutable_goal.py
uv run --extra dev python scripts/check_python_standards.py
if command -v docker >/dev/null 2>&1; then
  bash scripts/docker_check.sh
fi
bash scripts/terraform_check.sh
if command -v npm >/dev/null 2>&1; then
  (cd web && npm install --silent && npm run --silent test && npm run --silent verify:data-qid)
fi
python - <<'PY'
import json
from pathlib import Path
receipt = {"schema":"openai_interview.verify.v1","status":"PASS","checks":["compileall","pytest","contracts","immutable-goal","python-standards","docker-check-if-docker","terraform-check","react-data-qid-if-npm"]}
Path('receipts/verification.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
