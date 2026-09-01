"""Environment-backed settings for the control-plane demo."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_INTERVIEW_", extra="ignore")

    api_key: str = "dev-key"
    memory_url: str = "http://127.0.0.1:8601"
    agent_skills_root: str = "/home/graham/workspace/experiments/agent-skills"
    enable_hack_verify: bool = False
    request_timeout_seconds: float = Field(default=10.0, gt=0, le=60)


settings = Settings()
