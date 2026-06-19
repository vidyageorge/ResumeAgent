"""Agent orchestrator — routes messages to specialized agents."""

from __future__ import annotations

import re
import uuid

from vidya_copilot.llm.ollama_client import OllamaClient
from vidya_copilot.memory.store import MemoryStore
from vidya_copilot.prompts.system import AGENT_PROMPTS
from vidya_copilot.tools.registry import ToolRegistry


class AgentOrchestrator:
    INTENT_KEYWORDS = {
        "coding": [
            "framework", "selenium", "playwright", "pytest", "test case", "pom",
            "page object", "locator", "refactor", "bug", "unit test", "api test",
            "convert", "generate code", "review code", "fix", "debug",
        ],
        "interview": [
            "interview", "quiz me", "mock interview", "practice question",
            "score my answer", "technical question",
        ],
        "learning": [
            "teach me", "explain rag", "what is embedding", "vector database",
            "learning plan", "ai concept", "llm", "agentic", "quiz",
        ],
        "career": [
            "resume", "linkedin", "cover letter", "job application", "career",
            "optimize profile", "tailor resume", "professional email",
        ],
        "productivity": [
            "work hours", "track goal", "note", "reminder", "learning goal",
            "calculate hours", "productivity",
        ],
    }

    TOOL_ENABLED_AGENTS = {"coding", "general"}

    def __init__(
        self,
        llm: OllamaClient,
        memory: MemoryStore,
        tools: ToolRegistry,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.tools = tools

    def detect_agent(self, message: str, explicit_agent: str | None = None) -> str:
        if explicit_agent and explicit_agent in AGENT_PROMPTS:
            return explicit_agent
        lower = message.lower()
        scores = {agent: 0 for agent in self.INTENT_KEYWORDS}
        for agent, keywords in self.INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    scores[agent] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"

    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        agent_type: str | None = None,
    ) -> dict:
        session_id = session_id or str(uuid.uuid4())
        agent = self.detect_agent(message, agent_type)

        self.memory.save_message(session_id, "user", message, agent)
        history = self.memory.get_history(session_id)
        memory_context = self.memory.get_context_for_prompt()

        system = AGENT_PROMPTS[agent]
        system += f"\n\n## Long-term Memory\n{memory_context}"

        if agent in self.TOOL_ENABLED_AGENTS:
            reply = await self.llm.run_with_tools(
                system_prompt=system,
                user_message=message,
                tools=self.tools.get_tools(),
                tool_schemas=self.tools.get_schemas(),
                history=history,
            )
        else:
            messages = [{"role": "system", "content": system}]
            messages.extend(history[-10:])
            messages.append({"role": "user", "content": message})
            reply = await self.llm.chat(messages)

        self._auto_remember(message, reply, agent)
        self.memory.save_message(session_id, "assistant", reply, agent)

        return {
            "reply": reply,
            "session_id": session_id,
            "agent": agent,
        }

    def _auto_remember(self, message: str, reply: str, agent: str) -> None:
        remember_match = re.search(r"remember\s+(?:that\s+)?(.+)", message, re.I)
        if remember_match:
            self.memory.set_memory("user_notes", f"note_{hash(message) % 10000}", remember_match.group(1))

        if agent == "learning" and "progress" in message.lower():
            topic_match = re.search(r"(rag|embedding|agentic|llm|ai engineering)", message, re.I)
            if topic_match:
                self.memory.update_learning(topic_match.group(1), "in_progress", 10.0)
