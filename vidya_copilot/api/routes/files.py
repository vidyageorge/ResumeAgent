"""File operation routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vidya_copilot.api.deps import verify_api_key

router = APIRouter(prefix="/api/files", tags=["files"])


class ReadRequest(BaseModel):
    path: str


class WriteRequest(BaseModel):
    path: str
    content: str


class EditRequest(BaseModel):
    path: str
    old_text: str
    new_text: str


class PathRequest(BaseModel):
    path: str


class RenameRequest(BaseModel):
    old_path: str
    new_path: str


def create_files_router(file_tools) -> APIRouter:
    @router.post("/read", dependencies=[Depends(verify_api_key)])
    async def read_file(request: ReadRequest):
        return {"content": file_tools.read_file(request.path)}

    @router.post("/write", dependencies=[Depends(verify_api_key)])
    async def write_file(request: WriteRequest):
        return {"result": file_tools.write_file(request.path, request.content)}

    @router.post("/edit", dependencies=[Depends(verify_api_key)])
    async def edit_file(request: EditRequest):
        return {"result": file_tools.edit_file(request.path, request.old_text, request.new_text)}

    @router.post("/delete", dependencies=[Depends(verify_api_key)])
    async def delete_file(request: PathRequest):
        return {"result": file_tools.delete_file(request.path)}

    @router.post("/rename", dependencies=[Depends(verify_api_key)])
    async def rename_file(request: RenameRequest):
        return {"result": file_tools.rename_file(request.old_path, request.new_path)}

    @router.get("/list", dependencies=[Depends(verify_api_key)])
    async def list_directory(path: str = "."):
        return {"listing": file_tools.list_directory(path)}

    return router
