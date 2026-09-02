"""FastAPI adapter for the OpenAI interview control-plane demo."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from fastapi import Body, Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response

from .contracts import (
    EvalBatchRequest,
    EvalBatchResult,
    EvalItemResult,
    HackAuditRequest,
    HackAuditResult,
    HackVerifyRequest,
    HackVerifyResult,
    Health,
    MemoryRecallRequest,
    MemoryRecallResult,
)
from .hack import HackGateway
from .memory import MemoryGateway
from .security import require_api_key
from .service import EvalService, stable_hash

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DESCRIPTION = """
### OpenAI-relevant safety control-plane demo

An inspectable, Memory-native interview harness for showing how public context,
client prep, defensive SAST, and retained evals become typed control-plane
operations without guessing OpenAI's internal priorities.

---

**30-second interview quickstart**

1. **Authorize** with `x-api-key: dev-key`.
2. **Run `POST /v1/eval/test-all`** for a zero-body readiness check.
3. **Open `POST /v1/memory/recall`** to inspect source-grounded OpenAI/privacy recall.
4. **Open `POST /v1/hack/audit`** to inspect bounded SAST receipt output.

---

**Skill chain architecture**

- `$curate-client`: prepares client-scoped OpenAI/privacy interview context.
- `$setup-project`: audits the repeatable project setup recipe.
- `$memory`: owns recall and durable evidence persistence.
- `$hack`: runs bounded defensive SAST and emits typed receipts.
- `$agentic-evals`: proves claim and seam coverage repeatedly.

---

> **Boundaries and non-claims**
>
> Operates strictly on public context and Graham-owned artifacts. Does **not**
> claim OpenAI internal priorities, exploitability, live cloud deployment, or
> authorization to scan external systems.
"""

DOCS_AGENT_SCRIPT = r"""
<script>
(() => {
  const routeQids = {
    'GET /health/live': 'swagger.operation.health-live',
    'POST /v1/memory/recall': 'swagger.operation.memory-recall',
    'POST /v1/eval/batch': 'swagger.operation.eval-batch',
    'POST /v1/eval/test-all': 'swagger.operation.eval-test-all',
    'POST /v1/hack/verify': 'swagger.operation.hack-verify',
    'POST /v1/hack/audit': 'swagger.operation.hack-audit',
    'GET /v1/meta/memory-recall-flow.svg': 'swagger.operation.memory-recall-flow-svg',
  };

  function text(node) {
    return (node?.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function annotateForAgents() {
    document.querySelector('a[href="/openapi.json"]')?.setAttribute('data-qid', 'swagger.openapi-json');
    for (const button of document.querySelectorAll('button')) {
      const label = text(button);
      if (label === 'Authorize') button.setAttribute('data-qid', 'swagger.authorize');
      if (label === 'Execute') button.setAttribute('data-qid', 'swagger.execute-visible');
      if (label === 'Try it out') button.setAttribute('data-qid', 'swagger.try-it-out-visible');
      if (label === 'Close') button.setAttribute('data-qid', 'swagger.modal.close');
      if (label === 'Apply credentials') button.setAttribute('data-qid', 'swagger.authorize.apply');
    }
    document.querySelector('.auth-container input')?.setAttribute('data-qid', 'swagger.authorize.api-key');
    document.querySelector('.auth-container button[type="submit"]')?.setAttribute('data-qid', 'swagger.authorize.apply');
    document.querySelector('.dialog-ux button[type="submit"]')?.setAttribute('data-qid', 'swagger.authorize.apply');
    document.querySelector('.dialog-ux .btn-done')?.setAttribute('data-qid', 'swagger.modal.close');

    for (const block of document.querySelectorAll('.opblock')) {
      const method = text(block.querySelector('.opblock-summary-method'));
      const path = text(block.querySelector('.opblock-summary-path')).replace(/\s+/g, '');
      const qid = routeQids[`${method} ${path}`];
      if (!qid) continue;
      block.setAttribute('data-qid', qid);
      block.querySelector('.opblock-summary')?.setAttribute('data-qid', `${qid}.summary`);
      for (const button of block.querySelectorAll('button')) {
        const label = text(button).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        if (label) button.setAttribute('data-qid', `${qid}.${label}`);
      }
    }
  }

  let last = null;
  async function checkOpenApi() {
    try {
      const res = await fetch('/openapi.json?reload=' + Date.now(), { cache: 'no-store' });
      if (!res.ok) return;
      const current = await res.text();
      if (last === null) {
        last = current;
      } else if (current !== last) {
        location.reload();
      }
    } catch (_) {
      // Server may be between uvicorn reloads; keep polling.
    }
  }

  setInterval(annotateForAgents, 500);
  setInterval(checkOpenApi, 1000);
  annotateForAgents();
  checkOpenApi();
})();
</script>
"""

TAGS_METADATA = [
    {"name": "System Health", "description": "Liveness probes and runtime health checks."},
    {"name": "Memory & Context Recall", "description": "Context recall via `$memory`."},
    {"name": "Agentic Safety Evals", "description": "Batch checks for claim and seam coverage."},
    {"name": "Defensive SAST & Audit", "description": "Bounded `$hack` SAST scans and audit receipts."},
    {"name": "Interview Visuals", "description": "Swagger-rendered visual aids generated from project skills."},
]

SWAGGER_UI_PARAMETERS = {
    "tryItOutEnabled": True,
    "displayRequestDuration": True,
    "docExpansion": "list",
}


def debugger_location(path: str, line: int = 1, symbol: str | None = None) -> dict:
    command = f"skills/debugger/run.sh open {path} --line {line} --bridge"
    if symbol:
        command = f"skills/debugger/run.sh open {path} --function {symbol} --bridge"
    return {
        "file": path,
        "line": line,
        "symbol": symbol or Path(path).name,
        "github_url": f"https://github.com/grahama1970/openai-interview/blob/main/{path}#L{line}",
        "debugger_open_command": command,
    }


def code_location(endpoint) -> dict:
    """Return one route-to-code locator for Swagger, agents, and `$debugger`."""
    source_file = Path(endpoint.__code__.co_filename).resolve()
    try:
        relative_source = source_file.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_source = source_file
    return debugger_location(str(relative_source), endpoint.__code__.co_firstlineno, endpoint.__name__)


def add_code_locations_to_openapi(app: FastAPI) -> None:
    """Expose source links plus debugger hints in `/openapi.json`."""
    default_openapi = app.openapi

    def openapi_with_code_locations() -> dict:
        schema = default_openapi()
        for route in app.routes:
            endpoint = getattr(route, "endpoint", None)
            path = getattr(route, "path", "")
            if endpoint is None or path not in schema.get("paths", {}):
                continue
            location = code_location(endpoint)
            for method in getattr(route, "methods", set()):
                operation = schema["paths"][path].get(method.lower())
                if operation is not None:
                    operation["x-code-location"] = location
                    operation["externalDocs"] = {
                        "description": "View source handler",
                        "url": location["github_url"],
                    }
                    if path == "/v1/meta/memory-recall-flow.svg":
                        artifact = debugger_location("docs/visuals/memory_recall_flow.svg")
                        operation["x-artifact-location"] = artifact
                        operation["externalDocs"] = {
                            "description": "View SVG source",
                            "url": artifact["github_url"],
                        }
        return schema

    app.openapi = openapi_with_code_locations


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenAI Interview Control Plane",
        version="0.1.0",
        description=DESCRIPTION,
        docs_url=None,
        openapi_tags=TAGS_METADATA,
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
    )
    memory = MemoryGateway()
    evals = EvalService(memory)
    hack = HackGateway(memory)

    @app.get("/docs", include_in_schema=False)
    def docs() -> HTMLResponse:
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        )
        html = response.body.decode("utf-8").replace("</body>", f"{DOCS_AGENT_SCRIPT}</body>")
        return HTMLResponse(html)

    @app.get(
        "/v1/meta/memory-recall-flow.svg",
        response_class=Response,
        responses={200: {"content": {"image/svg+xml": {}}}},
        tags=["Interview Visuals"],
        summary="Render the Memory recall flow",
        description="Returns the `$create-svg` generated diagram that explains how a Swagger request becomes a `$memory recall` result without app-owned database writes.",
    )
    def memory_recall_flow_svg() -> Response:
        svg = files("openai_interview").joinpath("static/memory_recall_flow.svg").read_text()
        return Response(content=svg, media_type="image/svg+xml")

    @app.get(
        "/health/live",
        response_model=Health,
        tags=["System Health"],
        summary="Check control-plane health",
        description="Confirms the local FastAPI interview service is running before demonstrating Memory, eval, or Hack routes.",
    )
    def live() -> Health:
        return Health()

    @app.post(
        "/v1/memory/recall",
        response_model=MemoryRecallResult,
        dependencies=[Depends(require_api_key)],
        tags=["Memory & Context Recall"],
        summary="Recall OpenAI/privacy interview context",
        description="Queries `$memory` for source-grounded OpenAI/privacy prep-pack evidence. The app does not talk to ArangoDB or Qdrant directly.",
    )
    def recall(
        req: MemoryRecallRequest = Body(
            ...,
            openapi_examples={
                "openai_privacy_api_controls": {
                    "summary": "OpenAI privacy prep-pack recall",
                    "description": "Recalls client-scoped Q-A chunks curated by `$curate-client` and served through `$memory`.",
                    "value": {
                        "q": "OpenAI API data controls privacy engineering",
                        "scope": "client:openai-privacy",
                        "collections": ["lessons"],
                        "tags": ["openai-privacy-kb"],
                        "k": 3,
                        "classification": "internal",
                    },
                },
                "purpose_bound_access": {
                    "summary": "Purpose-bound access control",
                    "description": "Shows how the interview prep pack supports a concrete privacy-engineering design question.",
                    "value": {
                        "q": "How should purpose-bound access fail safely?",
                        "scope": "client:openai-privacy",
                        "collections": ["lessons"],
                        "tags": ["openai-privacy-kb"],
                        "k": 3,
                        "classification": "internal",
                    },
                },
            },
        ),
    ) -> MemoryRecallResult:
        return memory.recall(req)

    @app.post(
        "/v1/eval/batch",
        response_model=EvalBatchResult,
        dependencies=[Depends(require_api_key)],
        tags=["Agentic Safety Evals"],
        summary="Run a memory-first eval batch",
        description="Runs a small batch of claim/seam checks. Each item must start with `$memory`, so unsupported questions block instead of becoming ungrounded claims.",
    )
    def eval_batch(
        req: EvalBatchRequest = Body(
            ...,
            openapi_examples={
                "single_privacy_claim": {
                    "summary": "Single privacy claim check",
                    "description": "Runs one memory-first check and blocks if evidence is missing.",
                    "value": {
                        "batch_id": "swagger-demo-openai-privacy",
                        "purpose": "Show that interview claims are checked against Memory evidence.",
                        "items": [
                            {
                                "item_id": "api-data-controls",
                                "question": "OpenAI API data controls privacy engineering",
                                "probe_class": "memory_recall",
                                "skill_chain": ["memory"],
                                "classification": "internal",
                            }
                        ],
                        "memory_scope": "client:openai-privacy",
                        "tags": ["openai-privacy-kb"],
                        "persist_to_memory": False,
                        "classification": "internal",
                    },
                },
                "two_question_readiness_slice": {
                    "summary": "Two-question readiness slice",
                    "description": "Demonstrates a small batch without claiming the full retained eval suite ran through Swagger.",
                    "value": {
                        "batch_id": "swagger-demo-openai-readiness-slice",
                        "purpose": "Check two OpenAI/privacy interview questions against Memory evidence.",
                        "items": [
                            {
                                "item_id": "api-data-controls",
                                "question": "OpenAI API data controls privacy engineering",
                                "probe_class": "memory_recall",
                                "skill_chain": ["memory"],
                                "classification": "internal",
                            },
                            {
                                "item_id": "purpose-bound-access",
                                "question": "How should purpose-bound access fail safely?",
                                "probe_class": "memory_recall",
                                "skill_chain": ["memory"],
                                "classification": "internal",
                            },
                        ],
                        "memory_scope": "client:openai-privacy",
                        "tags": ["openai-privacy-kb"],
                        "persist_to_memory": False,
                        "classification": "internal",
                    },
                },
            },
        ),
    ) -> EvalBatchResult:
        return evals.run_batch(req)

    @app.post(
        "/v1/eval/test-all",
        response_model=EvalBatchResult,
        dependencies=[Depends(require_api_key)],
        tags=["Agentic Safety Evals"],
        summary="Test all demo boundaries",
        description="Zero-body readiness check for live demos. It exercises health, `$memory` recall, `$hack verify`, and `$hack audit`; Hack items block unless explicitly enabled.",
    )
    def eval_test_all() -> EvalBatchResult:
        results = [
            EvalItemResult(
                item_id="health-live",
                status="pass",
                request_hash=stable_hash({"path": "/health/live"}),
                finding="Health endpoint returned openai_interview.health.v1.",
                provider="fastapi",
            )
        ]
        memory_batch = evals.run_batch(EvalBatchRequest(
            batch_id="swagger-test-all",
            purpose="One-click Swagger readiness check for OpenAI/privacy interview demo.",
            items=[
                {
                    "item_id": "openai-privacy-memory",
                    "question": "OpenAI API data controls privacy engineering",
                    "skill_chain": ["memory"],
                    "classification": "internal",
                }
            ],
            memory_scope="client:openai-privacy",
            tags=["openai-privacy-kb"],
            persist_to_memory=False,
        ))
        results.extend(memory_batch.results)

        verify = hack.verify(HackVerifyRequest())
        results.append(EvalItemResult(
            item_id="hack-verify",
            status=verify.status,
            request_hash=stable_hash({"path": "/v1/hack/verify"}),
            finding="Hack verify passed." if verify.status == "pass" else "Hack verify did not pass; see typed error.",
            receipt_refs=[verify.receipt] if verify.receipt else [],
            provider="hack",
            error=verify.error,
        ))

        audit = hack.audit(HackAuditRequest(persist_to_memory=False))
        results.append(EvalItemResult(
            item_id="hack-audit",
            status=audit.status,
            request_hash=stable_hash({"path": "/v1/hack/audit", "target_kind": audit.target_kind, "tool": audit.tool}),
            finding=f"Hack audit returned {audit.finding_count} findings and {audit.high_count} high findings.",
            receipt_refs=[ref for ref in [audit.output_path, audit.receipt_ref] if ref],
            provider="hack",
            error=audit.error,
        ))

        status = "fail" if any(row.status == "fail" for row in results) else "blocked" if any(row.status == "blocked" for row in results) else "pass"
        return EvalBatchResult(batch_id="swagger-test-all", status=status, results=results)

    @app.post(
        "/v1/hack/verify",
        response_model=HackVerifyResult,
        dependencies=[Depends(require_api_key)],
        tags=["Defensive SAST & Audit"],
        summary="Verify the bounded Hack route",
        description="Runs `$hack verify` only when explicitly enabled. This is a local defensive safety gate, not an OpenAI-system scan.",
    )
    def hack_verify(
        req: HackVerifyRequest = Body(
            ...,
            openapi_examples={
                "default_verify": {
                    "summary": "Default Hack safety verify",
                    "description": "Runs `$hack verify` when `OPENAI_INTERVIEW_ENABLE_HACK_VERIFY=true`.",
                    "value": {"classification": "internal"},
                },
                "explicit_output_dir": {
                    "summary": "Verify with explicit artifact directory",
                    "description": "Writes the Hack verification receipt under a disposable local path.",
                    "value": {"artifact_root": "/tmp/openai-interview-hack-verify", "classification": "internal"},
                },
            },
        ),
    ) -> HackVerifyResult:
        return hack.verify(req)

    @app.post(
        "/v1/hack/audit",
        response_model=HackAuditResult,
        dependencies=[Depends(require_api_key)],
        tags=["Defensive SAST & Audit"],
        summary="Generate a SAST audit receipt",
        description="Runs containerized `$hack audit` against Graham-owned demo targets only when explicitly enabled, then returns the typed audit receipt summary.",
    )
    def hack_audit(
        req: HackAuditRequest = Body(
            ...,
            openapi_examples={
                "demo_vulnerable_python": {
                    "summary": "Demo vulnerable Python audit",
                    "description": "Containerized Bandit scan of the synthetic CWE-78 fixture; no Memory write.",
                    "value": {
                        "target_kind": "demo_vulnerable_python",
                        "tool": "bandit",
                        "severity": "low",
                        "persist_to_memory": False,
                        "memory_collection": "openai_interview_hack_scans",
                        "classification": "internal",
                    },
                },
                "self_semgrep": {
                    "summary": "Self repository Semgrep audit",
                    "description": "Containerized Semgrep scan of this Graham-owned repo. Use when there is time for a slightly broader local check.",
                    "value": {
                        "target_kind": "self",
                        "tool": "semgrep",
                        "severity": "medium",
                        "persist_to_memory": False,
                        "memory_collection": "openai_interview_hack_scans",
                        "classification": "internal",
                    },
                },
            },
        ),
    ) -> HackAuditResult:
        return hack.audit(req)

    add_code_locations_to_openapi(app)
    return app


app = create_app()
