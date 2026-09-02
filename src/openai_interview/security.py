"""API-key guard for local demo endpoints."""
from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from .settings import settings

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def require_api_key(x_api_key: str | None = Security(api_key_header)) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
