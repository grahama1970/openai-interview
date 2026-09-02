"""FastAPI adapter for the OpenAI interview control-plane demo."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import shlex
import subprocess

from fastapi import Body, Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response

from .contracts import (
    DebuggerOpenRequest,
    DebuggerOpenResult,
    EvalBatchRequest,
    EvalBatchResult,
    EvalItemResult,
    HackAuditRequest,
    HackAuditResult,
    HackVerifyRequest,
    HackVerifyResult,
    Health,
    ControlPlaneError,
    MemoryRecallRequest,
    MemoryRecallResult,
)
from .hack import HackGateway
from .memory import MemoryGateway
from .routes.brave_search import router as brave_search_router
from .routes.playground import router as playground_router
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
5. **Open [POST /v1/playground/sample-task](#/Interview%20Playground/sample_task_v1_playground_sample_task_post)** when the interview shifts into live endpoint design.

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
<script src="https://unpkg.com/lucide@latest"></script>
<style>
  .lucide { vertical-align: middle; width: 16px; height: 16px; display: inline-block; }
  .agent-source-sync .lucide { margin-right: 4px; }
</style>
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
    'POST /v1/meta/debugger/open': 'swagger.operation.debugger-open',
    'GET /v1/brave-search/star-wars/obscure-characters': 'swagger.operation.brave-star-wars-obscure-characters',
    'POST /v1/playground/sample-task': 'swagger.operation.playground-sample-task',
    'GET /v1/playground/tasks/{task_id}': 'swagger.operation.playground-read-task',
  };

  function text(node) {
    return (node?.textContent || '').replace(/\s+/g, ' ').trim();
  }

  let operationsByKey = {};

  function ensurePlaygroundBanner() {
    if (document.querySelector('[data-qid="swagger.playground-banner"]')) return;
    const info = document.querySelector('.information-container .info');
    if (!info) return;
    const banner = document.createElement('div');
    banner.setAttribute('data-qid', 'swagger.playground-banner');
    banner.style.cssText = 'margin:12px 0;padding:12px 14px;border:2px solid #8b5cf6;border-radius:8px;background:#faf5ff;font-size:14px;line-height:1.45';
    banner.innerHTML = '<strong><i data-lucide="sparkles"></i> Interview Playground</strong><br><a data-qid="swagger.open-playground" href="#/Interview%20Playground/sample_task_v1_playground_sample_task_post">Open /v1/playground/sample-task</a> to copy-paste a route template, run live JSON requests, and reshape endpoints as the interview flows.';
    info.appendChild(banner);
    window.lucide?.createIcons();
  }

  function operationKey(block) {
    const method = text(block.querySelector('.opblock-summary-method'));
    const path = text(block.querySelector('.opblock-summary-path')).replace(/\s+/g, '');
    return `${method} ${path}`;
  }

  function responseHref(operation, key) {
    const content = operation?.responses?.['200']?.content || {};
    const displayable = [
      'image/svg+xml',
      'image/png',
      'text/html',
      'text/markdown',
      'application/json',
    ].some((type) => content[type]);
    return displayable && key.startsWith('GET ') ? key.slice(4) : null;
  }

  async function openDebugger(command, statusNode) {
    const savedKey = localStorage.getItem('openai-interview-api-key') || '';
    const apiKey = savedKey || prompt('x-api-key for local debugger sync', 'dev-key') || '';
    if (!apiKey) return;
    localStorage.setItem('openai-interview-api-key', apiKey);
    statusNode.textContent = 'syncing...';
    const res = await fetch('/v1/meta/debugger/open', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': apiKey },
      body: JSON.stringify({ debugger_open_command: command, classification: 'internal' }),
    });
    const body = await res.json().catch(() => ({}));
    if (res.status === 401) localStorage.removeItem('openai-interview-api-key');
    statusNode.textContent = res.ok ? 'VS Code selected' : (body?.error?.message || body?.detail || 'sync failed');
  }

  function syncButton(qid, target, command) {
    return `<button type="button" class="agent-sync-button" data-sync-command="${command}" data-sync-target="${target}" data-qid="${qid}.sync-${target}" style="margin-left:8px;padding:3px 8px;border:1px solid #94a3b8;border-radius:5px;background:white;cursor:pointer"><i data-lucide="mouse-pointer-click"></i> Sync ${target} to VS Code</button>`;
  }

  function appendSourceSyncPanel(block, key, qid) {
    const operation = operationsByKey[key];
    if (!operation || block.querySelector(':scope > [data-qid$=".source-sync"]')) return;
    const handler = operation['x-code-location'];
    const artifact = operation['x-artifact-location'];
    const response = responseHref(operation, key);
    if (!handler && !artifact && !response) return;

    const panel = document.createElement('div');
    panel.className = 'agent-source-sync';
    panel.setAttribute('data-qid', `${qid}.source-sync`);
    panel.style.cssText = 'margin:10px 20px;padding:12px;border:1px solid #d8dde7;border-radius:6px;background:#f7fbff;font-size:13px;line-height:1.45';
    const rows = ['<strong><i data-lucide="waypoints"></i> Agent source sync</strong>'];
    if (handler) rows.push(`<i data-lucide="code-2"></i> Handler: <a data-qid="${qid}.source-handler" href="${handler.github_url}" target="_blank" rel="noreferrer">${handler.file}:${handler.line}</a>${syncButton(qid, 'handler', handler.debugger_open_command)}<br><i data-lucide="terminal"></i> <code data-qid="${qid}.debugger-handler">${handler.debugger_open_command}</code>`);
    if (artifact) rows.push(`<i data-lucide="file-code-2"></i> Artifact: <a data-qid="${qid}.source-artifact" href="${artifact.github_url}" target="_blank" rel="noreferrer">${artifact.file}:${artifact.line}</a>${syncButton(qid, 'artifact', artifact.debugger_open_command)}<br><i data-lucide="terminal"></i> <code data-qid="${qid}.debugger-artifact">${artifact.debugger_open_command}</code>`);
    if (response) rows.push(`<i data-lucide="chart-no-axes-combined"></i> Show: <a data-qid="${qid}.open-response" href="${response}" target="_blank" rel="noreferrer">open response</a>`);
    rows.push(`<span data-qid="${qid}.sync-status" style="color:#475569"></span>`);
    panel.innerHTML = rows.join('<div style="height:6px"></div>');
    for (const button of panel.querySelectorAll('.agent-sync-button')) {
      button.addEventListener('click', () => openDebugger(button.dataset.syncCommand, panel.querySelector(`[data-qid="${qid}.sync-status"]`)));
    }
    block.querySelector('.opblock-summary')?.after(panel);
    window.lucide?.createIcons();
  }

  function annotateForAgents() {
    ensurePlaygroundBanner();
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
      const key = operationKey(block);
      const qid = routeQids[key];
      if (!qid) continue;
      block.setAttribute('data-qid', qid);
      block.querySelector('.opblock-summary')?.setAttribute('data-qid', `${qid}.summary`);
      appendSourceSyncPanel(block, key, qid);
      for (const button of block.querySelectorAll('button')) {
        const label = text(button).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        if (label) button.setAttribute('data-qid', `${qid}.${label}`);
      }
    }
    window.lucide?.createIcons();
  }

  let last = null;
  async function checkOpenApi() {
    try {
      const res = await fetch('/openapi.json?reload=' + Date.now(), { cache: 'no-store' });
      if (!res.ok) return;
      const current = await res.text();
      const parsed = JSON.parse(current);
      operationsByKey = {};
      for (const [path, methods] of Object.entries(parsed.paths || {})) {
        for (const [method, operation] of Object.entries(methods || {})) {
          operationsByKey[`${method.toUpperCase()} ${path}`] = operation;
        }
      }
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
  window.lucide?.createIcons();
})();
</script>
"""

EVAL_BATCH_DESCRIPTION = """
<i data-lucide="shield-check"></i> **Run a memory-first eval batch**

Runs a small batch of claim/seam checks. Each item must start with `$memory`, so unsupported questions block instead of becoming ungrounded claims.

---

<span style="display: flex; align-items: center; gap: 6px;">
  <i data-lucide="code-2"></i> <strong>Source Handler:</strong>
  <code>src/openai_interview/main.py::eval_batch</code>
</span>

<span style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
  <i data-lucide="terminal"></i> <code>skills/debugger/run.sh open src/openai_interview/main.py --function eval_batch --bridge</code>
</span>
"""

MEMORY_RECALL_FLOW_DESCRIPTION = """
<i data-lucide="image"></i> **Memory Recall Diagram (SVG)**

Renders the `$create-svg` visual sequence diagram for memory-native context recall operations.

---

<span style="display: flex; align-items: center; gap: 6px;">
  <i data-lucide="file-code-2"></i> <strong>Artifact:</strong> <code>docs/visuals/memory_recall_flow.svg</code>
</span>

<span style="display: flex; align-items: center; gap: 6px; margin-top: 4px;">
  <i data-lucide="terminal"></i> <code>skills/debugger/run.sh open docs/visuals/memory_recall_flow.svg --line 1 --bridge</code>
</span>
"""

TAGS_METADATA = [
    {"name": "System Health", "description": "Liveness probes and runtime health checks."},
    {"name": "Memory & Context Recall", "description": "Context recall via `$memory`."},
    {"name": "Agentic Safety Evals", "description": "Batch checks for claim and seam coverage."},
    {"name": "Defensive SAST & Audit", "description": "Bounded `$hack` SAST scans and audit receipts."},
    {"name": "Interview Visuals", "description": "Swagger-rendered visual aids generated from project skills."},
    {"name": "Brave Search", "description": "Raw `$brave-search` powered discovery endpoints with Pydantic-shaped results."},
    {"name": "Interview Playground", "description": "Copy-paste live-coding routes for reshaping the control plane during pairing."},
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


def openapi_routes(app: FastAPI) -> list:
    """Return direct routes plus deferred included-router children."""
    routes = list(app.routes)
    for route in app.routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            routes.extend(original_router.routes)
    return routes


def allowed_debugger_commands(schema: dict) -> set[str]:
    """Return debugger commands that Swagger is allowed to run locally."""
    commands: set[str] = set()
    for methods in schema.get("paths", {}).values():
        for operation in methods.values():
            for key in ("x-code-location", "x-artifact-location"):
                command = (operation.get(key) or {}).get("debugger_open_command")
                if command:
                    commands.add(command)
    return commands


def add_code_locations_to_openapi(app: FastAPI) -> None:
    """Expose source links plus debugger hints in `/openapi.json`."""
    default_openapi = app.openapi

    def openapi_with_code_locations() -> dict:
        schema = default_openapi()
        for route in openapi_routes(app):
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
    app.include_router(brave_search_router)
    app.include_router(playground_router)

    @app.get("/docs", include_in_schema=False)
    def docs() -> HTMLResponse:
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        )
        html = response.body.decode("utf-8").replace("</body>", f"{DOCS_AGENT_SCRIPT}</body>")
        return HTMLResponse(html)

    @app.post(
        "/v1/meta/debugger/open",
        response_model=DebuggerOpenResult,
        dependencies=[Depends(require_api_key)],
        tags=["Interview Visuals"],
        summary="Sync Swagger endpoint to VS Code",
        description="""
<i data-lucide="mouse-pointer-click"></i> **Open the selected endpoint in VS Code**

Runs only debugger commands already published by this service's own OpenAPI
`x-code-location` or `x-artifact-location` metadata.
""",
    )
    def debugger_open(
        req: DebuggerOpenRequest = Body(
            ...,
            openapi_examples={
                "playground_handler": {
                    "summary": "Open playground handler in VS Code",
                    "description": "Runs the exact command published by x-code-location for the playground route.",
                    "value": {
                        "debugger_open_command": "skills/debugger/run.sh open src/openai_interview/routes/playground.py --function sample_task --bridge",
                        "classification": "internal",
                    },
                }
            },
        ),
    ) -> DebuggerOpenResult:
        """Run an allowlisted `$debugger open` command for the Swagger sync button."""
        allowed = allowed_debugger_commands(app.openapi())
        if req.debugger_open_command not in allowed:
            return DebuggerOpenResult(
                status="fail",
                command=[],
                error=ControlPlaneError(code="debugger_command_not_allowlisted", message="debugger command is not published by OpenAPI metadata"),
            )
        command = shlex.split(req.debugger_open_command)
        try:
            result = subprocess.run(command, cwd=PROJECT_ROOT, check=False, capture_output=True, text=True, timeout=20)
        except Exception as exc:
            return DebuggerOpenResult(
                status="fail",
                command=command,
                error=ControlPlaneError(code="debugger_open_failed", message=str(exc)),
            )
        status_value = "pass" if result.returncode == 0 else "fail"
        return DebuggerOpenResult(
            status=status_value,
            command=command,
            stdout_tail=result.stdout[-1000:],
            stderr_tail=result.stderr[-1000:],
            error=None if result.returncode == 0 else ControlPlaneError(code="debugger_open_failed", message=f"exit {result.returncode}"),
        )

    @app.get(
        "/v1/meta/memory-recall-flow.svg",
        response_class=Response,
        responses={200: {"content": {"image/svg+xml": {}}}},
        tags=["Interview Visuals"],
        summary="Render the Memory recall flow",
        description=MEMORY_RECALL_FLOW_DESCRIPTION,
    )
    def memory_recall_flow_svg() -> Response:
        """Render the Lucide-marked Memory recall SVG documentation endpoint."""
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
        description=EVAL_BATCH_DESCRIPTION,
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
