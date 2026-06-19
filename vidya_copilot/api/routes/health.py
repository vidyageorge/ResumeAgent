"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter

from vidya_copilot.config import settings

router = APIRouter(tags=["health"])


def create_health_router(llm) -> APIRouter:
    @router.get("/health")
    async def health():
        ollama = await llm.health_check()
        return {
            "status": "ok",
            "service": "Vidya Copilot",
            "version": "0.1.0",
            "workspace": str(settings.workspace_path),
            "ollama": ollama,
        }

    return router
