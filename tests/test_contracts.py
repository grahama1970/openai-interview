from __future__ import annotations

import pytest

from openai_interview.contracts import EvalBatchRequest, EvalItemRequest
from openai_interview.service import stable_hash


def test_eval_contract_requires_memory_first() -> None:
    with pytest.raises(ValueError):
        EvalItemRequest(item_id='x', question='What is the safe persistence boundary?', skill_chain=['hack'])


def test_eval_batch_contract_has_classification() -> None:
    req = EvalBatchRequest.model_validate({
        'batch_id': 'b1',
        'purpose': 'Validate Memory-native eval control-plane request',
        'classification': 'internal',
        'items': [{
            'item_id': 'i1',
            'question': 'What evidence supports the Memory-native persistence choice?',
            'classification': 'internal',
        }],
    })
    assert req.classification == 'internal'
    assert req.items[0].skill_chain == ['memory']


def test_stable_hash_is_stable() -> None:
    assert stable_hash({'b': 2, 'a': 1}) == stable_hash({'a': 1, 'b': 2})
