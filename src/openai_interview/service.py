"""Framework-neutral service functions for eval batches."""
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
        batch = EvalBatchResult(batch_id=req.batch_id, status=overall, results=results)
        if req.persist_to_memory:
            doc = {
                "_key": req.batch_id,
                "schema": "openai_interview.eval_batch_receipt.v1",
                "kind": "openai_interview_eval_batch_receipt",
                "batch_id": req.batch_id,
                "purpose": req.purpose,
                "status": batch.status,
                "tags": req.tags,
                "classification": req.classification,
                "retrieval_text": f"{req.purpose} status={batch.status} tags={' '.join(req.tags)}",
                "result_count": len(batch.results),
                "results": [row.model_dump(mode="json") for row in batch.results],
            }
            ref = self.memory.store(req.memory_collection, doc)
            if ref:
                batch.receipt_refs.append(ref)
        return batch
