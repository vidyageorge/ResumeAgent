"""Codebase indexing and semantic search with ChromaDB."""

from __future__ import annotations

import hashlib
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from vidya_copilot.config import settings

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", ".idea", ".vscode", "data", "chroma",
}
CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt",
    ".json", ".yaml", ".yml", ".xml", ".md", ".txt", ".sql",
    ".feature", ".robot", ".html", ".css", ".scss", ".env.example",
}


class CodebaseIndexer:
    def __init__(self) -> None:
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self._embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._vectorstore: Chroma | None = None

    def _get_store(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name="vidya_codebase",
                embedding_function=self._embeddings,
                persist_directory=str(settings.chroma_path),
            )
        return self._vectorstore

    def _collect_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if path.stat().st_size > 500_000:
                continue
            files.append(path)
        return files

    def index_project(self, project_path: str | None = None) -> dict:
        root = Path(project_path) if project_path else settings.workspace_path
        root = root.resolve()
        if not root.exists():
            return {"error": f"Path not found: {root}", "indexed": 0}

        files = self._collect_files(root)
        documents: list[Document] = []

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel_path = str(file_path.relative_to(root))
            doc_id = hashlib.md5(f"{root}:{rel_path}".encode()).hexdigest()
            chunks = self._splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": rel_path,
                            "project": str(root),
                            "chunk": i,
                            "doc_id": f"{doc_id}_{i}",
                            "language": file_path.suffix,
                        },
                    )
                )

        store = self._get_store()
        if documents:
            store.add_documents(documents)

        return {
            "project": str(root),
            "files_scanned": len(files),
            "chunks_indexed": len(documents),
        }

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        k = top_k or settings.rag_top_k
        store = self._get_store()
        try:
            results = store.similarity_search_with_score(query, k=k)
        except Exception:
            return []
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "project": doc.metadata.get("project", ""),
                "score": float(score),
            }
            for doc, score in results
        ]

    def find_symbol_usage(self, symbol: str, project_path: str | None = None) -> list[dict]:
        root = Path(project_path) if project_path else settings.workspace_path
        matches: list[dict] = []
        for file_path in self._collect_files(root.resolve()):
            try:
                lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                if symbol in line:
                    matches.append({
                        "file": str(file_path.relative_to(root.resolve())),
                        "line": i,
                        "content": line.strip(),
                    })
        return matches[:50]
