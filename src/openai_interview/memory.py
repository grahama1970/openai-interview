"""HTTP gateway for Memory-native recall."""
from __future__ import annotations

import httpx

from typing import Any

from .contracts import ControlPlaneError, MemoryRecallRequest, MemoryRecallResult
from .settings import settings


class MemoryGateway:
    def __init__(self, base_url: str = settings.memory_url) -> None:
        self.base_url = base_url.rstrip("/")

    def recall(self, req: MemoryRecallRequest) -> MemoryRecallResult:
        try:
            with httpx.Client(base_url=self.base_url, timeout=settings.request_timeout_seconds) as client:
                response = client.post(
                    "/recall",
                    json={
                        "q": req.q,
                        "scope": req.scope,
                        "collections": req.collections,
                        "tags": req.tags,
                        "k": req.k,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return MemoryRecallResult(
                status="blocked",
                error=ControlPlaneError(code="memory_unavailable", message=str(exc)),
            )
        return MemoryRecallResult(
            status="pass" if data.get("found") else "blocked",
            found=bool(data.get("found")),
            should_scan=bool(data.get("should_scan", True)),
            confidence=float(data.get("confidence", 0.0) or 0.0),
            item_count=len(data.get("items", [])),
            items=data.get("items", [])[: req.k],
        )

    def store(self, collection: str, document: dict[str, Any]) -> str | None:
        try:
            with httpx.Client(base_url=self.base_url, timeout=settings.request_timeout_seconds) as client:
                response = client.post("/store", json={"collection": collection, "document": document})
                response.raise_for_status()
                data = response.json()
        except Exception:
            return None
        return data.get("_id") or data.get("id") or data.get("key") or document.get("_key")
