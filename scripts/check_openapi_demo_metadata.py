#!/usr/bin/env python3
"""Verify Swagger/OpenAPI metadata tells the interview story."""
from __future__ import annotations

from fastapi.testclient import TestClient

from openai_interview.main import SWAGGER_UI_PARAMETERS, app

client = TestClient(app)
openapi = client.get("/openapi.json").json()
docs_html = client.get("/docs").text
info = openapi["info"]
description = info.get("description") or ""
for text in (
    "OpenAI-relevant safety control-plane demo",
    "30-second interview quickstart",
    "POST /v1/eval/test-all",
    "x-api-key: dev-key",
    "$curate-client",
    "$setup-project",
    "$memory",
    "$hack",
    "$agentic-evals",
    "Does **not**",
):
    assert text in description, text

expected_tags = {
    "System Health",
    "Memory & Context Recall",
    "Agentic Safety Evals",
    "Defensive SAST & Audit",
    "Interview Visuals",
}
assert {tag["name"] for tag in openapi.get("tags", [])} == expected_tags
assert SWAGGER_UI_PARAMETERS["tryItOutEnabled"] is True
assert SWAGGER_UI_PARAMETERS["displayRequestDuration"] is True
assert SWAGGER_UI_PARAMETERS["docExpansion"] == "list"
assert "APIKeyHeader" in openapi["components"]["securitySchemes"]
assert "/openapi.json?reload=" in docs_html
assert "data-qid" in docs_html
assert "swagger.operation.eval-test-all" in docs_html

ops = {
    (method.upper(), path): op
    for path, methods in openapi["paths"].items()
    for method, op in methods.items()
}
expected = {
    ("GET", "/health/live"): "System Health",
    ("POST", "/v1/memory/recall"): "Memory & Context Recall",
    ("POST", "/v1/eval/batch"): "Agentic Safety Evals",
    ("POST", "/v1/eval/test-all"): "Agentic Safety Evals",
    ("POST", "/v1/hack/verify"): "Defensive SAST & Audit",
    ("POST", "/v1/hack/audit"): "Defensive SAST & Audit",
    ("GET", "/v1/meta/memory-recall-flow.svg"): "Interview Visuals",
}
for key, tag in expected.items():
    op = ops[key]
    assert op["tags"] == [tag]
    assert op.get("summary")
    assert op.get("description")
    code_location = op.get("x-code-location") or {}
    assert code_location.get("file") == "src/openai_interview/main.py"
    assert code_location.get("symbol")
    assert code_location.get("github_url", "").startswith("https://github.com/grahama1970/openai-interview/blob/main/src/openai_interview/main.py#L")
    if key != ("GET", "/v1/meta/memory-recall-flow.svg"):
        assert op.get("externalDocs", {}).get("url") == code_location.get("github_url")
    assert "skills/debugger/run.sh open" in code_location.get("debugger_open_command", "")

svg_operation = ops[("GET", "/v1/meta/memory-recall-flow.svg")]
artifact_location = svg_operation.get("x-artifact-location") or {}
assert artifact_location.get("file") == "docs/visuals/memory_recall_flow.svg"
assert artifact_location.get("debugger_open_command") == "skills/debugger/run.sh open docs/visuals/memory_recall_flow.svg --line 1 --bridge"
assert svg_operation.get("externalDocs", {}).get("url") == artifact_location.get("github_url")

for key in [k for k in expected if k[0] == "POST"]:
    op = ops[key]
    if "requestBody" in op:
        content = op["requestBody"]["content"]["application/json"]
        assert content.get("examples"), key
    assert op["security"] == [{"APIKeyHeader": []}], key

print("OPENAPI_DEMO_METADATA_OK")
