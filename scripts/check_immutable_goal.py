"""Validate the immutable OpenAI interview goal contract."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ImmutableGoal(BaseModel):
    """Typed, minimal project goal contract."""

    model_config = ConfigDict(extra="forbid")

    schema_: str = Field(alias="schema")
    classification: str
    goal: str
    must: list[str] = Field(min_length=1)
    must_not: list[str] = Field(min_length=1)
    primary_proof: str
    proof_commands: list[str] = Field(min_length=1)


ROOT = Path(__file__).resolve().parents[1]
goal = ImmutableGoal.model_validate(json.loads((ROOT / "immutable_goal.json").read_text()))
assert goal.schema_ == "openai_interview.immutable_goal.v1"
assert goal.classification
assert any("$memory" in item for item in goal.must)
assert any("OpenAI internal" in item for item in goal.must_not)
assert goal.primary_proof == "receipts/agentic/interview-ready.json"
print("IMMUTABLE_GOAL_OK")
