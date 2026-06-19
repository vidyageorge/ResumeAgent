"""FastAPI dependency injection."""

from __future__ import annotations

from fastapi import Header, HTTPException

from vidya_copilot.config import settings


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
