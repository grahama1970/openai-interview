from __future__ import annotations

from fastapi.testclient import TestClient

from openai_interview.contracts import HackAuditResult, MemoryRecallResult
from openai_interview.main import create_app


class FakeMemory:
    def recall(self, _req):
        return MemoryRecallResult(status='pass', found=True, should_scan=False, confidence=0.9, item_count=1, items=[{'_key': 'lesson1'}])

    def store(self, collection, document):
        assert collection in {'openai_interview_receipts', 'openai_interview_hack_scans'}
        assert document['classification'] == 'internal'
        return f'{collection}/b1'


class FakeHack:
    def __init__(self, _memory=None):
        pass

    def audit(self, req):
        return HackAuditResult(
            status='pass',
            target_kind=req.target_kind,
            tool=req.tool,
            command=['hack', 'audit'],
            finding_count=1,
            high_count=1,
            cwes=['CWE-78'],
            receipt_ref='openai_interview_hack_scans/b1',
        )


def test_health_live() -> None:
    client = TestClient(create_app())
    response = client.get('/health/live')
    assert response.status_code == 200
    assert response.json()['classification'] == 'public'


def test_auth_required() -> None:
    client = TestClient(create_app())
    response = client.post('/v1/eval/batch', json={})
    assert response.status_code == 401


def test_eval_batch_uses_memory(monkeypatch) -> None:
    from openai_interview import main as main_module

    monkeypatch.setattr(main_module, 'MemoryGateway', lambda: FakeMemory())
    client = TestClient(main_module.create_app())
    response = client.post('/v1/eval/batch', headers={'x-api-key': 'dev-key'}, json={
        'batch_id': 'b1',
        'purpose': 'Validate Memory-backed eval route',
        'classification': 'internal',
        'persist_to_memory': True,
        'items': [{
            'item_id': 'i1',
            'question': 'What evidence supports the Memory-native persistence choice?',
            'classification': 'internal',
        }],
    })
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'pass'
    assert body['results'][0]['memory_refs'] == ['lesson1']
    assert body['receipt_refs'] == ['openai_interview_receipts/b1']


def test_hack_audit_endpoint(monkeypatch) -> None:
    from openai_interview import main as main_module

    monkeypatch.setattr(main_module, 'HackGateway', FakeHack)
    client = TestClient(main_module.create_app())
    response = client.post('/v1/hack/audit', headers={'x-api-key': 'dev-key'}, json={
        'target_kind': 'demo_vulnerable_python',
        'classification': 'internal',
    })
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'pass'
    assert body['finding_count'] == 1
    assert body['cwes'] == ['CWE-78']
    assert body['receipt_ref'] == 'openai_interview_hack_scans/b1'
