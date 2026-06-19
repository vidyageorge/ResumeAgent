"""Safe terminal command execution."""

from __future__ import annotations

import asyncio
import os
import shlex
from pathlib import Path

from vidya_copilot.config import settings

BLOCKED_PATTERNS = [
    "rm -rf /", "format ", "del /s", "shutdown", "reboot",
    ":(){ :|:& };:", "mkfs", "> /dev/sd",
]
ALLOWED_PREFIXES = [
    "pytest", "python", "pip", "playwright", "npx", "npm", "yarn",
    "git", "dir", "ls", "cd", "type", "cat", "echo", "node",
    "mvn", "gradle", "java", "dotnet", "uv", "ruff", "black",
    "mypy", "flake8", "allure", "docker", "curl", "wget",
]


class TerminalTools:
    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = (workspace or settings.workspace_path).resolve()

    def _validate_command(self, command: str) -> str | None:
        lower = command.lower().strip()
        for blocked in BLOCKED_PATTERNS:
            if blocked in lower:
                return f"Blocked dangerous command pattern: {blocked}"
        first_token = lower.split()[0] if lower.split() else ""
        if first_token and not any(first_token.startswith(p) for p in ALLOWED_PREFIXES):
            return (
                f"Command '{first_token}' not in allowlist. "
                f"Allowed: {', '.join(ALLOWED_PREFIXES)}"
            )
        return None

    async def run_command(self, command: str, cwd: str | None = None) -> str:
        error = self._validate_command(command)
        if error:
            return error

        work_dir = self.workspace
        if cwd:
            work_dir = (self.workspace / cwd).resolve()
            if not str(work_dir).startswith(str(self.workspace)):
                return "Working directory outside workspace."

        try:
            if os.name == "nt":
                proc = await asyncio.create_subprocess_shell(
                    command,
                    cwd=str(work_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *shlex.split(command),
                    cwd=str(work_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=settings.command_timeout_seconds,
            )
            output = stdout.decode(errors="replace").strip()
            errors = stderr.decode(errors="replace").strip()
            status = f"Exit code: {proc.returncode}"
            parts = [status]
            if output:
                parts.append(f"STDOUT:\n{output[-8000:]}")
            if errors:
                parts.append(f"STDERR:\n{errors[-4000:]}")
            return "\n".join(parts)
        except asyncio.TimeoutError:
            return f"Command timed out after {settings.command_timeout_seconds}s"
        except Exception as exc:
            return f"Execution error: {exc}"

    async def run_pytest(self, path: str = ".", extra_args: str = "-v") -> str:
        return await self.run_command(f"pytest {path} {extra_args}")

    async def run_playwright(self, path: str = ".", extra_args: str = "") -> str:
        return await self.run_command(f"npx playwright test {path} {extra_args}")

    async def git_status(self) -> str:
        return await self.run_command("git status")

    async def git_diff(self, args: str = "") -> str:
        return await self.run_command(f"git diff {args}")
