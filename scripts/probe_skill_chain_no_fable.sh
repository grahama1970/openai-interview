#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

missing=0
for path in \
  skills/brave-search/SKILL.md \
  skills/memory/SKILL.md \
  skills/hack/SKILL.md \
  skills/agentic-evals/SKILL.md \
  skills/best-practices-fastapi/SKILL.md \
  skills/terraform/SKILL.md \
  skills/ops-terraform/SKILL.md; do
  if [[ ! -e "$path" ]]; then
    echo "missing $path" >&2
    missing=1
  fi
done
[[ "$missing" == 0 ]]

python3 - <<'PY'
import json
from pathlib import Path
paths = [
    Path('README.md'),
    *[p for p in Path('scripts').glob('*.sh') if p.name != 'probe_skill_chain_no_fable.sh'],
    *Path('src').rglob('*.py'),
    *Path('tests').rglob('*.py'),
    *Path('web/src').rglob('*'),
]
text = '\n'.join(p.read_text(errors='ignore') for p in paths if p.is_file())
forbidden = ['claude-' + 'fable', 'handler-claude-' + 'fable', 'Fable 5', 'requires Fable', 'require Fable']
hits = [word for word in forbidden if word in text]
assert not hits, hits
readme = Path('README.md').read_text()
assert 'FastAPI/React code is the demo surface for that skill chain. It is not the point by itself.' in readme
fixture = json.loads(Path('fixtures/agentic_eval.json').read_text())
claim_ids = {claim['id'] for claim in fixture['capability_claims']}
assert 'openai_interview.skill_chain' in claim_ids
assert 'openai_interview.no_fable_dependency' in claim_ids
assert any(case['name'] == 'skill-chain-no-fable-dependency' for case in fixture['cases'])
print(json.dumps({'schema':'openai_interview.probe.no_fable.v1','status':'PASS','checked_files':len(paths),'required_skills':7}))
PY
