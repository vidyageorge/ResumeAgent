"""Terminal execution routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vidya_copilot.api.deps import verify_api_key

router = APIRouter(prefix="/api/terminal", tags=["terminal"])


class CommandRequest(BaseModel):
    command: str
    cwd: str | None = None


class TestRequest(BaseModel):
    path: str = "."
    extra_args: str = "-v"


def create_terminal_router(terminal_tools) -> APIRouter:
    @router.post("/run", dependencies=[Depends(verify_api_key)])
    async def run_command(request: CommandRequest):
        output = await terminal_tools.run_command(request.command, request.cwd)
        return {"output": output}

    @router.post("/pytest", dependencies=[Depends(verify_api_key)])
    async def run_pytest(request: TestRequest):
        output = await terminal_tools.run_pytest(request.path, request.extra_args)
        return {"output": output}

    @router.post("/playwright", dependencies=[Depends(verify_api_key)])
    async def run_playwright(request: TestRequest):
        output = await terminal_tools.run_playwright(request.path, request.extra_args)
        return {"output": output}

    @router.get("/git/status", dependencies=[Depends(verify_api_key)])
    async def git_status():
        output = await terminal_tools.git_status()
        return {"output": output}

    return router
