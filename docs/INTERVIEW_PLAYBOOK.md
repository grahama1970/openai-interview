# OpenAI interview playbook

## One-line thesis

Graham uses skills as an evidence operating system: public context comes from `$brave-search`, state comes from `$memory`, defensive cyber checks come from `$hack`, deployment handoff comes from `$terraform`/`$ops-terraform`, and `$agentic-evals` proves the chain without Fable.

## Five-minute walkthrough

1. **Context** — OpenAI's public privacy and safety material makes capability boundaries, access, safeguards, and proof boundaries worth discussing without guessing internal priorities.
2. **Swagger surface** — open `/docs`, use **Authorize** with `dev-key`, run `POST /v1/eval/test-all` for the zero-body readiness check, and open `GET /v1/meta/memory-recall-flow.svg` for the Swagger-rendered `$create-svg` Memory flow. Agents can target Swagger with injected `data-qid` markers and can jump from `/openapi.json` `x-code-location` hints to endpoint code through `$debugger`.
3. **FastAPI surface** — `src/openai_interview/main.py` exposes typed endpoints for health, Memory recall, eval batches, Hack verify, Hack audit, and the one-click demo check.
4. **Contracts** — `src/openai_interview/contracts.py` makes every request/response JSON and Pydantic-validated, including `classification`.
5. **Memory** — `src/openai_interview/memory.py` uses Memory HTTP endpoints; ArangoDB and Qdrant are behind `$memory`, not app dependencies.
6. **Hack** — `src/openai_interview/hack.py` calls `$hack audit` for bounded SAST only, then reads Hack-owned `hack.audit_receipt.v1` output.
7. **Docker** — `Dockerfile` and `docker-compose.yml` run the API as `appuser`, expose `/health/live`, and keep audit powers disabled in the container by default.
8. **Terraform** — `infra/terraform` is a plan-only handoff checked by `$ops-terraform`; it does not apply infrastructure.
9. **Proof** — `fixtures/agentic_eval.json` proves the skill chain, no-Fable dependency, Swagger metadata, Memory, Hack, Docker, Terraform, UI qids, and hot reload.

## If asked why this matters for OpenAI

High-stakes AI systems need more than clever model use. They need capability boundaries, safe tool access, auditable receipts, and evals that fail when a seam regresses. This artifact shows that Graham builds that way by default.

## If asked whether Tau or an agent can drive it

Yes. Treat `/openapi.json` as the machine-facing contract. Tau can orchestrate calls as typed tool steps and `$memory` remains the persistence/recall boundary behind the API. Do not add a custom chat widget to Swagger unless an interviewer specifically asks for an embedded operator chat; it adds UI code without improving the proof story.

## If asked whether Fable is required

No. The retained eval includes `skill-chain-no-fable-dependency`, and the proof is local: scripts, receipts, Memory readback, Docker health, Hack SAST, and Terraform validation.

## If asked what is not proven

This does not prove OpenAI internal priorities, production readiness, Azure deployment, exploitability, or authorization to scan OpenAI systems. It proves Graham's skill-chain method on a Graham-owned artifact.
