"""Vidya Copilot FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from vidya_copilot.agents.orchestrator import AgentOrchestrator
from vidya_copilot.api.routes.chat import create_chat_router
from vidya_copilot.api.routes.codebase import create_codebase_router
from vidya_copilot.api.routes.files import create_files_router
from vidya_copilot.api.routes.health import create_health_router
from vidya_copilot.api.routes.memory import create_memory_router
from vidya_copilot.api.routes.terminal import create_terminal_router
from vidya_copilot.config import settings
from vidya_copilot.llm.ollama_client import OllamaClient
from vidya_copilot.memory.database import init_db
from vidya_copilot.memory.store import MemoryStore
from vidya_copilot.rag.indexer import CodebaseIndexer
from vidya_copilot.rag.retriever import CodeRetriever
from vidya_copilot.tools.file_tools import FileTools
from vidya_copilot.tools.registry import ToolRegistry
from vidya_copilot.tools.terminal_tools import TerminalTools

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "copilot"

# Shared services
session_factory = init_db()
memory = MemoryStore(session_factory)
llm = OllamaClient()
indexer = CodebaseIndexer()
retriever = CodeRetriever(indexer)
file_tools = FileTools()
terminal_tools = TerminalTools()
tool_registry = ToolRegistry(file_tools, terminal_tools, retriever, indexer)
orchestrator = AgentOrchestrator(llm, memory, tool_registry)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.data_path.mkdir(parents=True, exist_ok=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Vidya Copilot",
    description="Personal local AI assistant — Cursor alternative",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_health_router(llm))
app.include_router(create_chat_router(orchestrator))
app.include_router(create_codebase_router(indexer, retriever, memory))
app.include_router(create_files_router(file_tools))
app.include_router(create_terminal_router(terminal_tools))
app.include_router(create_memory_router(memory))

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Vidya Copilot API", "docs": "/docs"}


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            session_id = data.get("session_id")
            agent = data.get("agent")
            if not message:
                await websocket.send_json({"reply": "Please send a message."})
                continue
            try:
                result = await orchestrator.chat(message, session_id, agent)
                await websocket.send_json(result)
            except Exception as exc:
                await websocket.send_json({
                    "reply": (
                        f"**Error:** {exc}\n\n"
                        "**Fix:** Start Ollama, then run:\n"
                        "```\nollama pull qwen3:8b\n```\n"
                        "Keep the Ollama app running and try again."
                    ),
                    "session_id": session_id or "",
                    "agent": agent or "general",
                })
    except WebSocketDisconnect:
        pass


def run():
    import uvicorn

    uvicorn.run(
        "vidya_copilot.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
