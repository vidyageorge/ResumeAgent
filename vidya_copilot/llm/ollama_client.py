"""Ollama LLM client with tool-calling loop."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

import httpx

from vidya_copilot.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except httpx.ConnectError:
            raise ConnectionError(
                "Cannot connect to Ollama at "
                f"{self.base_url}. Start the Ollama app and run: ollama pull {self.model}"
            ) from None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ConnectionError(
                    f"Model '{self.model}' not found. Run: ollama pull {self.model}"
                ) from None
            raise

    async def run_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        tools: dict[str, Callable[..., Any]],
        tool_schemas: list[dict],
        history: list[dict[str, str]] | None = None,
        max_iterations: int | None = None,
    ) -> str:
        max_iter = max_iterations or settings.max_tool_iterations
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_message})

        tools_description = json.dumps(tool_schemas, indent=2)
        messages[0]["content"] += (
            f"\n\n## Available Tools\n"
            f"When you need a tool, respond with ONLY a JSON block:\n"
            f'{{"tool": "tool_name", "args": {{...}}}}\n'
            f"Available tools:\n{tools_description}\n"
            f"When done, respond with normal text (no JSON)."
        )

        for _ in range(max_iter):
            reply = await self.chat(messages)
            tool_call = self._parse_tool_call(reply)
            if not tool_call:
                return reply

            tool_name = tool_call.get("tool", "")
            tool_args = tool_call.get("args", {})
            if tool_name not in tools:
                result = f"Unknown tool: {tool_name}"
            else:
                try:
                    result = await self._execute_tool(tools[tool_name], tool_args)
                except Exception as exc:
                    result = f"Tool error: {exc}"

            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Tool result ({tool_name}):\n{result}"})

        return "Reached maximum tool iterations. Please refine your request."

    def _parse_tool_call(self, text: str) -> dict | None:
        match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            if "tool" in data:
                return data
        except json.JSONDecodeError:
            pass
        return None

    async def _execute_tool(self, func: Callable, args: dict) -> str:
        import asyncio
        import inspect

        if inspect.iscoroutinefunction(func):
            result = await func(**args)
        else:
            result = func(**args)
            if asyncio.iscoroutine(result):
                result = await result
        return str(result) if result is not None else "OK"

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = [m["name"] for m in response.json().get("models", [])]
                return {
                    "status": "ok",
                    "models": models,
                    "configured_model": self.model,
                    "model_available": any(self.model in m for m in models),
                }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
