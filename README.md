# OpenAI Interview Control Plane

Memory-native skills demo for an Astra-style cyber-safety eval control plane.

This is not OpenAI software and does not claim access to Astra internals. It shows how Graham works by composing skills: `$brave-search` grounds the public Astra context, `$memory` recalls and persists evidence, `$hack` runs bounded defensive scans, `$agentic-evals` proves seams repeatedly, and `$terraform`/`$ops-terraform` provide a plan-only deployment handoff.

The FastAPI/React code is the demo surface for that skill chain. It is not the point by itself.

## Skill chain

1. `$brave-search` grounds the OpenAI/Astra public context.
2. `$best-practices-fastapi` shapes framework-neutral Pydantic contracts and adapter boundaries.
3. `$memory` handles recall and durable evidence storage; ArangoDB/Qdrant stay behind Memory.
4. `$hack` runs authorized, containerized SAST and emits typed audit receipts.
5. `$agentic-evals` repeats the proof cases and checks claim/seam coverage.
6. `$terraform` and `$ops-terraform` keep deployment as a checked handoff, not an unproven apply.

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

## Skill links

`skills` is a symlink to `/home/graham/workspace/experiments/agent-skills/skills`, so local checks use the canonical `$memory`, `$hack`, `$terraform`, `$ops-terraform`, `$best-practices-fastapi`, `$best-practices-python`, and `$agentic-evals` implementations.

## Terraform handoff

```bash
scripts/docker_check.sh
scripts/terraform_check.sh
scripts/terraform_plan.sh  # prints the plan-only handoff; it never applies
scripts/probe_hack_audit_endpoint.sh  # proves FastAPI -> $hack audit -> $memory readback
```

## Verify

```bash
bash scripts/verify.sh
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh run fixtures/agentic_eval.json --output /tmp/openai-interview-agentic-eval.json
```
