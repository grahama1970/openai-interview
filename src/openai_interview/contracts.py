"""Pydantic contracts for the OpenAI interview control-plane demo."""
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
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "q": "OpenAI API data controls privacy engineering",
                    "scope": "client:openai-privacy",
                    "collections": ["lessons"],
                    "tags": ["openai-privacy-kb"],
                    "k": 3,
                    "classification": "internal",
                }
            ]
        },
    )

    q: str = Field(min_length=8, description="Question-shaped Memory recall query.")
    scope: str = Field(default="openai-interview", description="Memory scope for the interview/demo context.")
    collections: list[str] = Field(default_factory=lambda: ["lessons"], description="Memory collections to search.")
    tags: list[str] = Field(default_factory=lambda: ["openai-interview"], description="Memory tags that bound recall.")
    k: int = Field(default=5, ge=1, le=25, description="Maximum Memory items to return.")
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
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "batch_id": "swagger-demo-openai-privacy",
                    "purpose": "Show that interview claims are checked against Memory evidence.",
                    "items": [
                        {
                            "item_id": "api-data-controls",
                            "question": "OpenAI API data controls privacy engineering",
                            "probe_class": "memory_recall",
                            "skill_chain": ["memory"],
                            "classification": "internal",
                        }
                    ],
                    "memory_scope": "client:openai-privacy",
                    "tags": ["openai-privacy-kb"],
                    "persist_to_memory": False,
                    "classification": "internal",
                }
            ]
        },
    )

    batch_id: str = Field(min_length=1, max_length=128, description="Stable eval batch identifier.")
    purpose: str = Field(min_length=8, max_length=500, description="Why this eval batch exists.")
    items: list[EvalItemRequest] = Field(min_length=1, max_length=50, description="Memory-first checks to run.")
    memory_scope: str = "openai-interview"
    tags: list[str] = Field(default_factory=lambda: ["openai-interview", "cyber-safety"])
    persist_to_memory: bool = False
    memory_collection: str = "openai_interview_receipts"
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


class DebuggerOpenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debugger_open_command: str = Field(
        min_length=1,
        description="Exact command from OpenAPI x-code-location or x-artifact-location.",
    )
    classification: Classification = "internal"


class DebuggerOpenResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["openai_interview.debugger_open.v1"] = Field(
        default="openai_interview.debugger_open.v1",
        alias="schema",
    )
    status: Literal["pass", "fail"]
    command: list[str]
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: ControlPlaneError | None = None
    classification: Classification = "internal"


class HackVerifyRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"artifact_root": "/tmp/openai-interview-hack-verify", "classification": "internal"}
            ]
        },
    )

    artifact_root: str | None = Field(default=None, description="Optional local receipt output directory for `$hack verify`.")
    classification: Classification = "internal"


class HackAuditRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "target_kind": "demo_vulnerable_python",
                    "tool": "bandit",
                    "severity": "low",
                    "persist_to_memory": False,
                    "memory_collection": "openai_interview_hack_scans",
                    "classification": "internal",
                }
            ]
        },
    )

    target_kind: Literal["self", "demo_vulnerable_python"] = Field(default="demo_vulnerable_python", description="Graham-owned scan target for the bounded demo.")
    tool: Literal["bandit", "semgrep", "all"] = Field(default="bandit", description="Containerized SAST tool selection.")
    severity: Literal["low", "medium", "high"] = Field(default="low", description="Minimum reported severity.")
    persist_to_memory: bool = True
    memory_collection: str = "openai_interview_hack_scans"
    classification: Classification = "internal"


class HackAuditResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_: Literal["openai_interview.hack_audit.v1"] = Field(
        default="openai_interview.hack_audit.v1",
        alias="schema",
    )
    status: Status
    target_kind: str
    tool: str
    command: list[str]
    finding_count: int = 0
    high_count: int = 0
    cwes: list[str] = Field(default_factory=list)
    output_path: str | None = None
    receipt_ref: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: ControlPlaneError | None = None
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
