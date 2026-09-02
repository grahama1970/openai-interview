# OpenAI Interview Control Plane

Memory-native skills demo for an Astra-style cyber-safety eval control plane.

This is not OpenAI software and does not claim access to Astra internals. It shows how Graham works by composing skills: `$brave-search` grounds the public Astra context, `$curate-client` can turn supplied public/client materials into a reusable prep pack, `$memory` recalls and persists evidence, `$hack` runs bounded defensive scans, `$agentic-evals` proves seams repeatedly, and `$terraform`/`$ops-terraform` provide a plan-only deployment handoff.

The FastAPI/React code is the demo surface for that skill chain. It is not the point by itself.

## Start here

| Need | Start with |
| --- | --- |
| Five-minute interview story | `docs/INTERVIEW_PLAYBOOK.md` |
| Immutable scope | `immutable_goal.json` |
| API contracts | `src/openai_interview/contracts.py` |
| FastAPI endpoints | `src/openai_interview/main.py` |
| Memory boundary | `src/openai_interview/memory.py` |
| Hack SAST boundary | `src/openai_interview/hack.py` |
| React operator surface | `web/` |
| Docker runtime handoff | `Dockerfile`, `docker-compose.yml`, `scripts/docker_check.sh` |
| Terraform handoff | `infra/terraform/`, `scripts/terraform_check.sh`, `scripts/terraform_plan.sh` |
| Retained proof | `fixtures/agentic_eval.json`, `receipts/agentic/interview-ready.json` |

## Skill chain

1. `$brave-search` grounds the OpenAI/Astra public context.
2. `$curate-client` is the prep-pack entry point when official OpenAI pages, interview notes, or recruiter-supplied material need to become reusable, Memory-ready client context. This repo does not vendor that source corpus; it shows where the curated packet enters the chain.
3. `$best-practices-readme` keeps this README navigable, evidence-aware, and explicit about non-claims.
4. `$best-practices-fastapi` shapes framework-neutral Pydantic contracts and adapter boundaries.
5. `$memory` handles recall and durable evidence storage; ArangoDB/Qdrant stay behind Memory.
6. `$hack` runs authorized, containerized SAST and emits typed audit receipts.
7. `$agentic-evals` repeats the proof cases and checks claim/seam coverage.
8. `$terraform` and `$ops-terraform` keep deployment as a checked handoff, not an unproven apply.

## Demo surface

- `contracts.py`: Pydantic request/response/receipt models.
- `service.py`: framework-neutral logic.
- `memory.py`: `$memory` HTTP adapter; ArangoDB/Qdrant stay behind Memory.
- `hack.py`: bounded `$hack verify` plus `$hack audit` integration. The audit route is disabled unless `OPENAI_INTERVIEW_ENABLE_HACK_AUDIT=true` and only accepts `self` or `demo_vulnerable_python` targets.
- `main.py`: FastAPI adapter.
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
| OpenAI/Astra internals | Only public context and Graham-owned artifacts were used. |
| Production readiness | This is an interview demo and handoff, not a production deployment. |
| Azure deployment | Terraform is plan-only; no cloud apply was run. |
| Exploitability | `$hack` SAST findings are defensive signals, not exploit proof. |
| Authorization to scan OpenAI systems | The scan target is this Graham-owned repo/demo only. |

## Skill links

`skills` is a symlink to `/home/graham/workspace/experiments/agent-skills/skills`, so local checks use the canonical `$memory`, `$hack`, `$terraform`, `$ops-terraform`, `$best-practices-fastapi`, `$best-practices-python`, `$best-practices-react`, `$best-practices-readme`, and `$agentic-evals` implementations.
