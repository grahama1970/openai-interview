from __future__ import annotations

import hashlib
import json

from .contracts import EvalBatchRequest, EvalBatchResult, EvalItemResult, MemoryRecallRequest
from .memory import MemoryGateway


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


class EvalService:
    def __init__(self, memory: MemoryGateway | None = None) -> None:
        self.memory = memory or MemoryGateway()

    def run_batch(self, req: EvalBatchRequest) -> EvalBatchResult:
        results: list[EvalItemResult] = []
        for item in req.items:
            recall = self.memory.recall(MemoryRecallRequest(
                q=item.question,
                scope=req.memory_scope,
                collections=["lessons"],
                tags=req.tags,
                k=5,
                classification=item.classification,
            ))
            refs = [row.get("_id") or row.get("_key") for row in recall.items]
            refs = [ref for ref in refs if ref]
            status = "pass" if recall.found else "blocked"
            results.append(EvalItemResult(
                item_id=item.item_id,
                status=status,
                request_hash=stable_hash(item.model_dump(mode="json")),
                finding=(
                    f"Memory returned {recall.item_count} items with confidence {recall.confidence}."
                    if recall.found else
                    "Memory did not return enough evidence; scan/research is required."
                ),
                memory_refs=refs,
                error=recall.error,
                classification=item.classification,
            ))
        overall = "pass" if all(row.status == "pass" for row in results) else "blocked"
        return EvalBatchResult(batch_id=req.batch_id, status=overall, results=results)
