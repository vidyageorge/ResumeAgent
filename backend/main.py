"""FastAPI server with REST and WebSocket chat endpoints."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.agent import ChatAgent
from backend.config import settings
from backend.naukri_bot import NaukriBot

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

bot = NaukriBot()
agent = ChatAgent(bot)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    if bot.is_active:
        await bot.stop()


app = FastAPI(title="Naukri Job Agent", lifespan=lifespan)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
async def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Naukri Job Agent API. POST /chat or connect via WebSocket /ws"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "browser_active": bot.is_active,
        "logged_in": bot.is_logged_in,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = await agent.handle_message(request.message)
    return ChatResponse(reply=reply)


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json({"reply": "Please send a message."})
                continue
            reply = await agent.handle_message(message)
            await websocket.send_json({"reply": reply})
    except WebSocketDisconnect:
        pass


def run():
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
