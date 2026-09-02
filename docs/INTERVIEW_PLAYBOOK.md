# OpenAI interview playbook

## One-line thesis

Graham uses skills as an evidence operating system: public context comes from `$brave-search`, state comes from `$memory`, defensive cyber checks come from `$hack`, deployment handoff comes from `$terraform`/`$ops-terraform`, and `$agentic-evals` proves the chain without Fable.

## Five-minute walkthrough

1. **Context** — OpenAI's public Astra posts make cyber capability a control-plane problem: capability, access, safeguards, and proof boundaries.
2. **FastAPI surface** — `src/openai_interview/main.py` exposes typed endpoints for health, Memory recall, eval batches, Hack verify, and Hack audit.
3. **Contracts** — `src/openai_interview/contracts.py` makes every request/response JSON and Pydantic-validated, including `classification`.
4. **Memory** — `src/openai_interview/memory.py` uses Memory HTTP endpoints; ArangoDB and Qdrant are behind `$memory`, not app dependencies.
5. **Hack** — `src/openai_interview/hack.py` calls `$hack audit` for bounded SAST only, then reads Hack-owned `hack.audit_receipt.v1` output.
6. **Docker** — `Dockerfile` and `docker-compose.yml` run the API as `appuser`, expose `/health/live`, and keep audit powers disabled in the container by default.
7. **Terraform** — `infra/terraform` is a plan-only handoff checked by `$ops-terraform`; it does not apply infrastructure.
8. **Proof** — `fixtures/agentic_eval.json` proves the skill chain, no-Fable dependency, Memory, Hack, Docker, Terraform, UI qids, and hot reload.

## If asked why this matters for OpenAI

Astra-level systems need more than clever model use. They need capability boundaries, safe tool access, auditable receipts, and evals that fail when a seam regresses. This artifact shows that Graham builds that way by default.

## If asked whether Fable is required

No. The retained eval includes `skill-chain-no-fable-dependency`, and the proof is local: scripts, receipts, Memory readback, Docker health, Hack SAST, and Terraform validation.

## If asked what is not proven

This does not prove OpenAI/Astra internals, production readiness, Azure deployment, exploitability, or authorization to scan OpenAI systems. It proves Graham's skill-chain method on a Graham-owned artifact.
