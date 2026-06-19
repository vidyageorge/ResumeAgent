"""Chat API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from vidya_copilot.api.deps import verify_api_key

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    agent: str | None = Field(
        default=None,
        description="Force agent: coding, interview, learning, career, productivity, general",
    )


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    agent: str


def create_chat_router(orchestrator) -> APIRouter:
    @router.post("", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
    async def chat(request: ChatRequest):
        result = await orchestrator.chat(
            message=request.message,
            session_id=request.session_id,
            agent_type=request.agent,
        )
        return ChatResponse(**result)

    @router.get("/agents")
    async def list_agents():
        return {
            "agents": [
                {"id": "coding", "name": "Coding Assistant", "description": "Frameworks, tests, POM, refactoring"},
                {"id": "interview", "name": "Interview Coach", "description": "Mock interviews with scoring"},
                {"id": "learning", "name": "AI Learning Coach", "description": "RAG, embeddings, agentic AI"},
                {"id": "career", "name": "Career Coach", "description": "Resume, LinkedIn, cover letters"},
                {"id": "productivity", "name": "Productivity", "description": "Notes, goals, work hours"},
                {"id": "general", "name": "General", "description": "Auto-routes to best agent"},
            ]
        }

    return router
