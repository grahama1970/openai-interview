"""Check the demo contract files without starting services."""
from __future__ import annotations

import json
from pathlib import Path

from openai_interview.contracts import EvalBatchRequest, HackAuditRequest

sample = json.loads(Path('fixtures/sample_eval_batch.json').read_text())
req = EvalBatchRequest.model_validate(sample)
assert req.items[0].skill_chain[0] == 'memory'
audit = HackAuditRequest.model_validate({'target_kind': 'demo_vulnerable_python', 'classification': 'internal'})
for model in [req, *req.items, audit]:
    assert model.classification
assert audit.target_kind == 'demo_vulnerable_python'
print('CONTRACTS_OK')
