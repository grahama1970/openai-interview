from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Classification = Literal["public", "internal", "confidential"]
Status = Literal["pass", "fail", "blocked"]


class Health(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_: Literal["openai_interview.health.v1"] = Field(
        default="openai_interview.health.v1",
        alias="schema",
    )
    status: Literal["ok"] = "ok"
    service: str = "openai-interview-control-plane"
    classification: Classification = "public"


class ControlPlaneError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    classification: Classification = "internal"


class MemoryRecallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str = Field(min_length=8)
    scope: str = "openai-interview"
    collections: list[str] = Field(default_factory=lambda: ["lessons"])
    tags: list[str] = Field(default_factory=lambda: ["openai-interview"])
    k: int = Field(default=5, ge=1, le=25)
    classification: Classification = "internal"


class MemoryRecallResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["openai_interview.memory_recall.v1"] = Field(
        default="openai_interview.memory_recall.v1",
        alias="schema",
    )
    status: Status
    found: bool = False
    should_scan: bool = True
    confidence: float = 0.0
    item_count: int = 0
    items: list[dict[str, Any]] = Field(default_factory=list)
    error: ControlPlaneError | None = None
    classification: Classification = "internal"


class EvalItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=8)
    probe_class: Literal["memory_recall", "hack_verify", "design_review"] = "memory_recall"
    skill_chain: list[str] = Field(default_factory=lambda: ["memory"])
    classification: Classification = "internal"

    @field_validator("skill_chain")
    @classmethod
    def memory_first(cls, value: list[str]) -> list[str]:
        if not value or value[0] != "memory":
            raise ValueError("skill_chain must start with memory")
        return value


class EvalBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=8, max_length=500)
    items: list[EvalItemRequest] = Field(min_length=1, max_length=50)
    memory_scope: str = "openai-interview"
    tags: list[str] = Field(default_factory=lambda: ["openai-interview", "cyber-safety"])
    classification: Classification = "internal"


class EvalItemResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    status: Status
    request_hash: str
    finding: str
    memory_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    provider: str = "memory"
    error: ControlPlaneError | None = None
    classification: Classification = "internal"


class EvalBatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["openai_interview.eval_batch.v1"] = Field(
        default="openai_interview.eval_batch.v1",
        alias="schema",
    )
    batch_id: str
    status: Status
    results: list[EvalItemResult]
    receipt_refs: list[str] = Field(default_factory=list)
    classification: Classification = "internal"


class HackVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_root: str | None = None
    classification: Classification = "internal"


class HackVerifyResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["openai_interview.hack_verify.v1"] = Field(
        default="openai_interview.hack_verify.v1",
        alias="schema",
    )
    status: Status
    receipt: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: ControlPlaneError | None = None
    classification: Classification = "internal"
