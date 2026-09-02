#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p receipts/agentic

./scripts/probe_skill_chain_no_fable.sh | tee /tmp/openai_interview_ready_no_fable.json
bash scripts/verify.sh | tee /tmp/openai_interview_ready_verify.log
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh run fixtures/agentic_eval.json --output /tmp/openai-interview-agentic-eval-ready.json
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh coverage show . > /tmp/openai-interview-agentic-coverage-ready.json
python3 - <<'PY'
import json
from pathlib import Path
report=json.loads(Path('/tmp/openai-interview-agentic-eval-ready.json').read_text())
coverage=json.loads(Path('/tmp/openai-interview-agentic-coverage-ready.json').read_text())
receipt={
  'schema':'openai_interview.interview_ready.v1',
  'status':'PASS',
  'eval_readiness':report.get('readiness'),
  'eval_outcomes':report.get('outcome_counts'),
  'case_count':report.get('case_count'),
  'trial_count':report.get('trial_count'),
  'coverage_verdict':coverage.get('summary',{}).get('verdict'),
  'critical_seams_covered':coverage.get('summary',{}).get('critical_seams_covered'),
  'critical_seams':coverage.get('summary',{}).get('critical_seams'),
  'proofs': [
    '/tmp/openai-interview-agentic-eval-ready.json',
    '/tmp/openai-interview-agentic-coverage-ready.json',
    'receipts/agentic/docker-check.json',
    'docs/INTERVIEW_PLAYBOOK.md',
  ],
}
assert receipt['eval_readiness'] == 'READY', receipt
assert receipt['coverage_verdict'] == 'READY', receipt
Path('receipts/agentic/interview-ready.json').write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt))
PY
