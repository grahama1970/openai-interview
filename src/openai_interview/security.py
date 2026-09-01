"""API-key guard for local demo endpoints."""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from .settings import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
