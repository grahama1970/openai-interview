"""Copy-paste playground routes for live interview endpoint design."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from openai_interview.contracts import Classification
from openai_interview.security import require_api_key

router = APIRouter(
    prefix="/v1/playground",
    tags=["Interview Playground"],
    dependencies=[Depends(require_api_key)],
)

# In-memory harness for live CRUD sketches. Replace with `$memory` only after the
# interview flow proves the endpoint belongs in the control plane.
db: dict[str, dict[str, Any]] = {}


class InterviewTaskRequest(BaseModel):
    """Starter request candidates can adapt during live pairing."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, examples=["Process memory recall batch"])
    input_data: dict[str, Any] = Field(default_factory=dict, examples=[{"key": "value"}])
    priority: int = Field(default=1, ge=1, le=5)
    classification: Classification = "internal"


class InterviewTaskResponse(BaseModel):
    """Starter response for quick Swagger-visible endpoint experiments."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    status: str = "completed"
    result: dict[str, Any]
    classification: Classification = "internal"


@router.post(
    "/sample-task",
    response_model=InterviewTaskResponse,
    summary="[Candidate] Sample Task Endpoint",
    description="""
<i data-lucide="sparkles"></i> **Interview Task Starter**

Copy this endpoint when the interview flow needs a new control-plane operation.
The imports, Pydantic models, auth dependency, Swagger docs, and in-memory state
harness are already present so pairing time goes into the logic.
""",
)
def sample_task(
    payload: InterviewTaskRequest = Body(
        ...,
        openapi_examples={
            "live_pairing_task": {
                "summary": "Live pairing starter",
                "description": "Small JSON payload candidates can mutate while designing a new endpoint.",
                "value": {
                    "title": "Process memory recall batch",
                    "input_data": {"question": "OpenAI API data controls privacy engineering"},
                    "priority": 2,
                    "classification": "internal",
                },
            }
        },
    ),
) -> InterviewTaskResponse:
    """Create one in-memory task and return the candidate-visible result."""
    task_id = f"task_{uuid4().hex[:8]}"
    result = {"processed_title": payload.title, "data": payload.input_data, "priority": payload.priority}
    db[task_id] = result
    return InterviewTaskResponse(task_id=task_id, result=result, classification=payload.classification)


@router.get(
    "/tasks/{task_id}",
    response_model=InterviewTaskResponse,
    summary="[Candidate] Read Playground Task",
    description="""
<i data-lucide="database"></i> **In-memory readback**

Shows the tiny state harness candidates can use before promoting durable state to `$memory`.
""",
)
def read_task(task_id: str) -> InterviewTaskResponse:
    """Read a task from the interview-only in-memory harness."""
    if task_id not in db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return InterviewTaskResponse(task_id=task_id, result=db[task_id])
