# OpenAI Interview Control Plane

Memory-native FastAPI interview artifact for an Astra-style cyber-safety eval control plane.

This is not OpenAI software and does not claim access to Astra internals. It shows Graham's method: typed Python contracts, Memory-backed evidence, bounded Hack gates, and retained eval proof.

## Shape

- `contracts.py`: Pydantic request/response/receipt models.
- `service.py`: framework-neutral logic.
- `memory.py`: `$memory` HTTP adapter; ArangoDB/Qdrant stay behind Memory.
- `hack.py`: bounded `$hack verify` integration.
- `main.py`: FastAPI adapter.

No PostgreSQL is used. Durable state goes through `$memory` endpoints.

## Run

```bash
cp .env.example .env
uv run --extra dev pytest
scripts/dev.sh      # FastAPI hot reload on 127.0.0.1:8080
scripts/dev-all.sh  # FastAPI hot reload + Vite React hot reload
```

## Verify

```bash
bash scripts/verify.sh
/home/graham/workspace/experiments/agent-skills/skills/agentic-evals/run.sh run fixtures/agentic_eval.json --output /tmp/openai-interview-agentic-eval.json
```
