"""Tool registry — binds tools to schemas for the agent."""

from __future__ import annotations

from typing import Any, Callable

from vidya_copilot.rag.indexer import CodebaseIndexer
from vidya_copilot.rag.retriever import CodeRetriever
from vidya_copilot.tools.file_tools import FileTools
from vidya_copilot.tools.framework_templates import get_framework_structure
from vidya_copilot.tools.terminal_tools import TerminalTools


class ToolRegistry:
    def __init__(
        self,
        file_tools: FileTools,
        terminal_tools: TerminalTools,
        code_retriever: CodeRetriever,
        indexer: CodebaseIndexer,
    ) -> None:
        self.file_tools = file_tools
        self.terminal_tools = terminal_tools
        self.code_retriever = code_retriever
        self.indexer = indexer

    def get_tools(self) -> dict[str, Callable[..., Any]]:
        return {
            "read_file": self.file_tools.read_file,
            "write_file": self.file_tools.write_file,
            "edit_file": self.file_tools.edit_file,
            "delete_file": self.file_tools.delete_file,
            "rename_file": self.file_tools.rename_file,
            "list_directory": self.file_tools.list_directory,
            "create_directory": self.file_tools.create_directory,
            "run_command": self.terminal_tools.run_command,
            "run_pytest": self.terminal_tools.run_pytest,
            "run_playwright": self.terminal_tools.run_playwright,
            "git_status": self.terminal_tools.git_status,
            "search_codebase": self.code_retriever.retrieve,
            "find_symbol": self.indexer.find_symbol_usage,
            "index_project": self.indexer.index_project,
            "scaffold_framework": self._scaffold_framework,
        }

    def get_schemas(self) -> list[dict]:
        return [
            {"name": "read_file", "description": "Read a file", "args": {"path": "string"}},
            {"name": "write_file", "description": "Write/create a file", "args": {"path": "string", "content": "string"}},
            {"name": "edit_file", "description": "Replace text in a file", "args": {"path": "string", "old_text": "string", "new_text": "string"}},
            {"name": "delete_file", "description": "Delete a file or directory", "args": {"path": "string"}},
            {"name": "rename_file", "description": "Rename a file", "args": {"old_path": "string", "new_path": "string"}},
            {"name": "list_directory", "description": "List directory contents", "args": {"path": "string (optional, default '.')"}},
            {"name": "create_directory", "description": "Create a directory", "args": {"path": "string"}},
            {"name": "run_command", "description": "Run shell command", "args": {"command": "string", "cwd": "string (optional)"}},
            {"name": "run_pytest", "description": "Run pytest", "args": {"path": "string", "extra_args": "string"}},
            {"name": "run_playwright", "description": "Run Playwright tests", "args": {"path": "string", "extra_args": "string"}},
            {"name": "git_status", "description": "Run git status", "args": {}},
            {"name": "search_codebase", "description": "Semantic code search", "args": {"query": "string"}},
            {"name": "find_symbol", "description": "Find symbol usage in code", "args": {"symbol": "string", "project_path": "string (optional)"}},
            {"name": "index_project", "description": "Index project for RAG", "args": {"project_path": "string (optional)"}},
            {"name": "scaffold_framework", "description": "Scaffold test framework (selenium/playwright/api)", "args": {"framework_type": "string", "base_path": "string"}},
        ]

    def _scaffold_framework(self, framework_type: str, base_path: str) -> str:
        structure = get_framework_structure(framework_type)
        return self.file_tools.generate_project_structure(base_path, structure)
