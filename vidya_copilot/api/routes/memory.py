"""Memory and notes routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vidya_copilot.api.deps import verify_api_key

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemorySetRequest(BaseModel):
    category: str
    key: str
    value: str


class NoteRequest(BaseModel):
    title: str
    content: str
    tags: str = ""


class LearningRequest(BaseModel):
    topic: str
    level: str = "beginner"
    progress_pct: float = 0.0
    notes: str = ""


def create_memory_router(memory) -> APIRouter:
    @router.get("", dependencies=[Depends(verify_api_key)])
    async def list_memory(category: str | None = None):
        return {"entries": memory.list_memory(category)}

    @router.post("/set", dependencies=[Depends(verify_api_key)])
    async def set_memory(request: MemorySetRequest):
        memory.set_memory(request.category, request.key, request.value)
        return {"status": "saved"}

    @router.get("/history/{session_id}", dependencies=[Depends(verify_api_key)])
    async def get_history(session_id: str, limit: int = 20):
        return {"messages": memory.get_history(session_id, limit)}

    @router.post("/notes", dependencies=[Depends(verify_api_key)])
    async def add_note(request: NoteRequest):
        note_id = memory.add_note(request.title, request.content, request.tags)
        return {"id": note_id}

    @router.get("/notes", dependencies=[Depends(verify_api_key)])
    async def list_notes(tag: str | None = None):
        return {"notes": memory.list_notes(tag)}

    @router.post("/learning", dependencies=[Depends(verify_api_key)])
    async def update_learning(request: LearningRequest):
        memory.update_learning(request.topic, request.level, request.progress_pct, request.notes)
        return {"status": "updated"}

    @router.get("/learning", dependencies=[Depends(verify_api_key)])
    async def get_learning():
        return {"progress": memory.get_learning_progress()}

    @router.get("/interviews", dependencies=[Depends(verify_api_key)])
    async def list_interviews(limit: int = 10):
        return {"sessions": memory.list_interviews(limit)}

    return router
