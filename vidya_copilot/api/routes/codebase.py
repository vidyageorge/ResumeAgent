"""Codebase indexing and search routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from vidya_copilot.api.deps import verify_api_key

router = APIRouter(prefix="/api/codebase", tags=["codebase"])


class IndexRequest(BaseModel):
    project_path: str | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8


class SymbolRequest(BaseModel):
    symbol: str
    project_path: str | None = None


def create_codebase_router(indexer, retriever, memory) -> APIRouter:
    @router.post("/index", dependencies=[Depends(verify_api_key)])
    async def index_project(request: IndexRequest):
        result = indexer.index_project(request.project_path)
        if "files_scanned" in result:
            memory.record_indexed_project(
                result.get("project", ""),
                result.get("files_scanned", 0),
            )
        return result

    @router.post("/search", dependencies=[Depends(verify_api_key)])
    async def search(request: SearchRequest):
        return {"results": indexer.search(request.query, request.top_k)}

    @router.post("/ask", dependencies=[Depends(verify_api_key)])
    async def ask_about_codebase(request: SearchRequest):
        context = retriever.answer_about_codebase(request.query)
        return {"context": context}

    @router.post("/symbol", dependencies=[Depends(verify_api_key)])
    async def find_symbol(request: SymbolRequest):
        return {"matches": indexer.find_symbol_usage(request.symbol, request.project_path)}

    return router
