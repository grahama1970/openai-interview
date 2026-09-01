"""FastAPI adapter for the OpenAI interview control-plane demo."""
from __future__ import annotations

from fastapi import Depends, FastAPI

from .contracts import EvalBatchRequest, EvalBatchResult, HackVerifyRequest, HackVerifyResult, Health, MemoryRecallRequest, MemoryRecallResult
from .hack import HackGateway
from .memory import MemoryGateway
from .security import require_api_key
from .service import EvalService


def create_app() -> FastAPI:
    app = FastAPI(title="OpenAI Interview Control Plane", version="0.1.0")
    memory = MemoryGateway()
    evals = EvalService(memory)
    hack = HackGateway()

    @app.get("/health/live", response_model=Health)
    def live() -> Health:
        return Health()

    @app.post("/v1/memory/recall", response_model=MemoryRecallResult, dependencies=[Depends(require_api_key)])
    def recall(req: MemoryRecallRequest) -> MemoryRecallResult:
        return memory.recall(req)

    @app.post("/v1/eval/batch", response_model=EvalBatchResult, dependencies=[Depends(require_api_key)])
    def eval_batch(req: EvalBatchRequest) -> EvalBatchResult:
        return evals.run_batch(req)

    @app.post("/v1/hack/verify", response_model=HackVerifyResult, dependencies=[Depends(require_api_key)])
    def hack_verify(req: HackVerifyRequest) -> HackVerifyResult:
        return hack.verify(req)

    return app


app = create_app()
