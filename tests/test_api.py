from __future__ import annotations

from fastapi.testclient import TestClient

from openai_interview.contracts import HackAuditResult, HackVerifyResult, MemoryRecallResult
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

    def verify(self, _req):
        return HackVerifyResult(status='pass', receipt='/tmp/hack-verify.json')

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


def test_swagger_docs_are_agent_operable() -> None:
    client = TestClient(create_app())
    docs = client.get('/docs')
    assert docs.status_code == 200
    assert '/openapi.json?reload=' in docs.text
    assert 'location.reload()' in docs.text
    assert 'data-qid' in docs.text
    assert 'appendSourceSyncPanel' in docs.text
    assert '.debugger-handler' in docs.text
    assert '.debugger-artifact' in docs.text
    assert 'swagger.operation.eval-test-all' in docs.text
    assert 'swagger.operation.memory-recall-flow-svg' in docs.text

    openapi = client.get('/openapi.json').json()
    operation = openapi['paths']['/v1/eval/test-all']['post']
    location = operation['x-code-location']
    assert location['file'] == 'src/openai_interview/main.py'
    assert location['symbol'] == 'eval_test_all'
    assert location['github_url'].startswith('https://github.com/grahama1970/openai-interview/blob/main/src/openai_interview/main.py#L')
    assert operation['externalDocs']['url'] == location['github_url']
    assert 'skills/debugger/run.sh open' in location['debugger_open_command']

    svg_operation = openapi['paths']['/v1/meta/memory-recall-flow.svg']['get']
    artifact = svg_operation['x-artifact-location']
    assert artifact['file'] == 'docs/visuals/memory_recall_flow.svg'
    assert artifact['debugger_open_command'] == 'skills/debugger/run.sh open docs/visuals/memory_recall_flow.svg --line 1 --bridge'
    assert svg_operation['externalDocs']['url'] == artifact['github_url']


def test_memory_recall_flow_svg_renders() -> None:
    client = TestClient(create_app())
    response = client.get('/v1/meta/memory-recall-flow.svg')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('image/svg+xml')
    assert '<title id="rsa-title">Memory recall flow</title>' in response.text
    assert 'APP NEVER WRITES RAW AQL OR EMBEDDINGS' in response.text


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


def test_eval_test_all_zero_body(monkeypatch) -> None:
    from openai_interview import main as main_module

    monkeypatch.setattr(main_module, 'MemoryGateway', lambda: FakeMemory())
    monkeypatch.setattr(main_module, 'HackGateway', FakeHack)
    client = TestClient(main_module.create_app())
    response = client.post('/v1/eval/test-all', headers={'x-api-key': 'dev-key'})
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'pass'
    assert [row['item_id'] for row in body['results']] == ['health-live', 'openai-privacy-memory', 'hack-verify', 'hack-audit']
