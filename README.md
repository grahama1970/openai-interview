# OpenAI Interview Control Plane

Memory-native skills demo for an OpenAI-relevant safety eval control plane.

This is not OpenAI software and does not claim access to OpenAI internal priorities. It shows how Graham works by composing skills: `$brave-search` grounds public OpenAI/privacy context, `$curate-client` can turn supplied public/client materials into a reusable prep pack, `$memory` recalls and persists evidence, `$hack` runs bounded defensive scans, `$agentic-evals` proves seams repeatedly, and `$terraform`/`$ops-terraform` provide a plan-only deployment handoff.

The FastAPI/React code is the demo surface for that skill chain. It is not the point by itself.

## Start here

| Need | Start with |
| --- | --- |
| Five-minute interview story | `docs/INTERVIEW_PLAYBOOK.md` |
| Immutable scope | `immutable_goal.json` |
| API contracts | `src/openai_interview/contracts.py` |
| FastAPI endpoints | `src/openai_interview/main.py` |
| Live endpoint playground | `src/openai_interview/routes/playground.py` |
| Memory boundary | `src/openai_interview/memory.py` |
| Hack SAST boundary | `src/openai_interview/hack.py` |
| React operator surface | `web/` |
| Docker runtime handoff | `Dockerfile`, `docker-compose.yml`, `scripts/docker_check.sh` |
| Terraform handoff | `infra/terraform/`, `scripts/terraform_check.sh`, `scripts/terraform_plan.sh` |
| Retained proof | `fixtures/agentic_eval.json`, `receipts/agentic/interview-ready.json` |

## Skill chain

1. `$brave-search` grounds public OpenAI/privacy context.
2. `$curate-client` is the prep-pack entry point when official OpenAI pages, interview notes, or recruiter-supplied material need to become reusable, Memory-ready client context. This repo does not vendor that source corpus; it shows where the curated packet enters the chain.
3. `$setup-project` captures the project recipe so the setup can be repeated instead of reconstructed from chat history.
4. `$best-practices-readme` keeps this README navigable, evidence-aware, and explicit about non-claims.
5. `$best-practices-fastapi` shapes framework-neutral Pydantic contracts and adapter boundaries.
6. `$memory` handles recall and durable evidence storage; ArangoDB/Qdrant stay behind Memory.
7. `$hack` runs authorized, containerized SAST and emits typed audit receipts.
8. `$agentic-evals` repeats the proof cases and checks claim/seam coverage.
9. `$terraform` and `$ops-terraform` keep deployment as a checked handoff, not an unproven apply.

## How this project was set up with skills

The setup is meant to be visible to interviewers. The point is not that a small FastAPI app exists; the point is that the repo was assembled as a repeatable skill chain with proof at each seam.

| Setup step | Skill | What it contributed | Where to inspect |
| --- | --- | --- | --- |
| Interview/client brief | `$curate-client` | OpenAI/privacy prep-pack path: official/client materials become Q-A chunks, Memory recall probes, and a live-evidence prep pack. Current plan evidence reports 98 sources, 16 briefing points, and a 220-question oracle. | `skills/curate-client/run.sh plan --config skills/curate-client/configs/openai_privacy_2026_09.yaml` |
| Targeted-question recall | `$curate-client` + `$memory` | Interviewers can ask pointed questions against the curated OpenAI/privacy brief and verify the oracle recalls client-scoped chunks. | `skills/curate-client/run.sh verify --config skills/curate-client/configs/openai_privacy_2026_09.yaml` |
| Project recipe | `$setup-project` | Read-only plan/audit showing the required skills, files, README terms, immutable goal, curate-client handoff, and assembly evidence. | `skills/setup-project/run.sh audit --config skills/setup-project/configs/openai_interview.yaml` |
| README | `$best-practices-readme` | Start-here navigation, skill provenance, proof table, and non-claims. | `README.md` |
| API shape | `$best-practices-fastapi` | Pydantic contracts, framework-neutral service layer, FastAPI adapter boundary. | `src/openai_interview/` |
| Persistence | `$memory` | Recall and durable evidence storage through Memory endpoints only. | `src/openai_interview/memory.py` |
| Defensive scan | `$hack` | Bounded SAST scan and Hack-owned receipt parsing. | `src/openai_interview/hack.py`, `receipts/agentic/hack-audit-endpoint.json` |
| Runtime handoff | Docker + `$ops-docker` pattern | Non-root, read-only local container with a healthcheck and disabled Hack powers by default. | `Dockerfile`, `docker-compose.yml`, `scripts/docker_check.sh` |
| Deployment handoff | `$terraform` / `$ops-terraform` | Plan-only Terraform module and backend-free validation. | `infra/terraform/`, `scripts/terraform_check.sh` |
| Proof | `$agentic-evals` | Repeated claim/seam evals, coverage, and interview readiness receipt. | `fixtures/agentic_eval.json`, `receipts/agentic/interview-ready.json` |

## Assembly evidence

`$setup-project audit` emits `setup_project.assembly_evidence.v1`: first commit, current commit, elapsed seconds, and commit count. That gives the interview story a receipt-backed timing/provenance field instead of a vague "quickly built" claim.

## Ask targeted questions

Interviewers can use the table above to ask focused questions instead of broad résumé questions. The exact read-only brief check is:

```bash
skills/curate-client/run.sh verify --config skills/curate-client/configs/openai_privacy_2026_09.yaml
```

That command verifies the curated OpenAI/privacy probes recall client-scoped chunks before any live-evidence use.

- How does `$curate-client` turn interview material into Memory-ready Q-A chunks?
- Where is the immutable goal enforced, and what does it forbid?
- What does the FastAPI layer own versus `service.py`?
- What proof says the app is Memory-native and not PostgreSQL-backed?
- Why is `$hack` limited to bounded SAST here?
- What does `$ops-terraform` validate, and what does it deliberately not do?
- Which `$agentic-evals` seam would fail if a future change removed one of these guarantees?

## Demo surface

Use `/docs` first in the interview. Swagger now carries the project explanation, endpoint grouping, one `Authorize` flow for `x-api-key`, named request examples, a zero-body `POST /v1/eval/test-all` readiness check, a Swagger-rendered `$create-svg` Memory recall flow at `GET /v1/meta/memory-recall-flow.svg`, a `$brave-search` demo at `GET /v1/brave-search/star-wars/obscure-characters`, agent-facing `data-qid` markers, Lucide icons for source/action cues, and debugger hints in `/openapi.json`. The React surface remains a fallback if the interviewer asks for an operator workflow instead of API inspection.

This is a control-plane starting point, not a finished fancy FastAPI endpoint service. The service is useful because each endpoint is tied back to inspectable code and skill artifacts: `x-code-location` points to the FastAPI handler, `x-artifact-location` points to generated artifacts such as SVG, Markdown, report, or chart files, and the custom Swagger page renders an Agent source sync panel with exact `$debugger open ... --bridge` commands. A project agent can read `/openapi.json`, select an endpoint in Swagger by `data-qid`, open the handler in VS Code, or open the artifact behind a chart/information endpoint without guessing where the code lives.

- `contracts.py`: Pydantic request/response/receipt models.
- `service.py`: framework-neutral logic.
- `memory.py`: `$memory` HTTP adapter; ArangoDB/Qdrant stay behind Memory.
- `hack.py`: bounded `$hack verify` plus `$hack audit` integration. The audit route is disabled unless `OPENAI_INTERVIEW_ENABLE_HACK_AUDIT=true` and only accepts `self` or `demo_vulnerable_python` targets.
- `main.py`: FastAPI adapter and custom Swagger/Lucide/source-sync docs surface.
- `routes/playground.py`: copy-paste live-coding router with Pydantic schemas, auth, and an in-memory `db` harness for endpoint experiments before promotion into durable `$memory` flows.
- `routes/brave_search.py`: `$brave-search` backed demo route that returns 30 Pydantic-validated obscure Star Wars character rows with `level`, `name`, `origin`, and `bio` fields.
- `web/`: React/Vite operator surface with `data-qid` checks.
- `Dockerfile` / `docker-compose.yml`: container handoff that runs as `appuser`, exposes health, and disables Hack powers by default.
- `infra/terraform/`: skill-scaffolded deployment handoff, checked by `$ops-terraform`.
- `docs/INTERVIEW_PLAYBOOK.md`: five-minute interview narrative centered on Graham's skill chain.

No PostgreSQL is used. Durable state goes through `$memory` endpoints.

## Run

```bash
cp .env.example .env
uv run --extra dev pytest
scripts/dev.sh      # FastAPI hot reload on 127.0.0.1:8080
scripts/dev-all.sh  # FastAPI hot reload + Vite React hot reload
scripts/docker_check.sh  # Docker build + container health proof
# Open http://127.0.0.1:8080/docs, click Authorize, enter dev-key,
# then run POST /v1/eval/test-all for the zero-body demo check.
```

## Verify

```bash
bash scripts/verify.sh
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh run fixtures/agentic_eval.json --output /tmp/openai-interview-agentic-eval.json
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh coverage show .
```

Current retained readiness proof lives at `receipts/agentic/interview-ready.json`.

## Docker and Terraform handoff

`docker-compose.yml` is the local runtime handoff: non-root container user, read-only filesystem, tmpfs `/tmp`, dropped Linux capabilities, `no-new-privileges`, healthcheck, and Hack powers disabled by default.

`$ops-terraform` does not validate Docker Compose. It validates the Terraform module in `infra/terraform/` with `fmt -check` and `terraform validate` using backend-free detection. The module carries the Docker handoff values (`container_image`, `container_port`, `memory_url`) as typed variables/outputs so a later deployment lane can consume them without this repo running `terraform apply`.

```bash
scripts/docker_check.sh
scripts/terraform_check.sh
scripts/terraform_plan.sh  # prints the plan-only handoff; it never applies
scripts/probe_hack_audit_endpoint.sh  # proves FastAPI -> $hack audit -> $memory readback
```

## Applied best-practices scope

| Area | Skill applied | Proof boundary |
| --- | --- | --- |
| README | `$best-practices-readme` | This file is a navigable map with proof and non-claims. |
| FastAPI | `$best-practices-fastapi` | Pydantic contracts and framework-neutral service boundaries. |
| Python | `$best-practices-python` | `scripts/check_python_standards.py` and project tests. |
| React | `$best-practices-react` | `web/scripts/verify-data-qid.mjs` checks operator controls. |
| Security scanning | `$hack` plus security best-practice boundaries | SAST only; no exploit proof. |
| Terraform detection | `$ops-terraform` | `scripts/terraform_check.sh` validates, no apply. |

This is not a claim of compliance with every `best-practices-*` skill in `agent-skills`; many are unrelated to this repo.

## Proof and non-claims

| Checked | Current artifact |
| --- | --- |
| Interview readiness | `receipts/agentic/interview-ready.json` |
| Docker health and non-root runtime | `receipts/agentic/docker-check.json` |
| Hack audit endpoint and Memory readback | `receipts/agentic/hack-audit-endpoint.json` |
| Hot reload probe | `receipts/agentic/hot-reload.json` |
| Terraform validation | `scripts/terraform_check.sh` |

| Not claimed | Reason |
| --- | --- |
| OpenAI internal priorities | Only public context and Graham-owned artifacts were used. |
| Production readiness | This is an interview demo and handoff, not a production deployment. |
| Azure deployment | Terraform is plan-only; no cloud apply was run. |
| Exploitability | `$hack` SAST findings are defensive signals, not exploit proof. |
| Authorization to scan OpenAI systems | The scan target is this Graham-owned repo/demo only. |

## Skill links

`skills` is a symlink to `/home/graham/workspace/experiments/agent-skills/skills`, so local checks use the canonical `$memory`, `$hack`, `$terraform`, `$ops-terraform`, `$best-practices-fastapi`, `$best-practices-python`, `$best-practices-react`, `$best-practices-readme`, and `$agentic-evals` implementations.
