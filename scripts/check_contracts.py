from __future__ import annotations

import json
from pathlib import Path

from openai_interview.contracts import EvalBatchRequest

sample = json.loads(Path('fixtures/sample_eval_batch.json').read_text())
req = EvalBatchRequest.model_validate(sample)
assert req.items[0].skill_chain[0] == 'memory'
for model in [req, *req.items]:
    assert model.classification
print('CONTRACTS_OK')
