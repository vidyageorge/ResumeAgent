"""Chat agent that interprets user prompts and drives the Naukri bot."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI

from backend.config import settings
from backend.naukri_bot import ApplyResult, JobListing, NaukriBot, parse_login_from_text


class Intent(str, Enum):
    START = "start"
    STOP = "stop"
    LOGIN = "login"
    SEARCH = "search"
    APPLY = "apply"
    APPLY_URL = "apply_url"
    STATUS = "status"
    HELP = "help"
    CHAT = "chat"


@dataclass
class ParsedCommand:
    intent: Intent
    keywords: str = ""
    location: str = ""
    max_count: int = 5
    url: str = ""
    email: str | None = None
    password: str | None = None
    raw_message: str = ""


SYSTEM_PROMPT = """You are a Naukri job application assistant. Parse the user's message into a JSON command.

Available intents:
- start: open the browser
- stop: close the browser
- login: sign in to Naukri
- search: search for jobs (extract keywords, location, max_count)
- apply: search and apply to jobs (extract keywords, location, max_count)
- apply_url: apply to a specific job URL
- status: show current session status
- help: show help
- chat: general conversation, not a Naukri action

Respond ONLY with valid JSON:
{
  "intent": "search",
  "keywords": "python developer",
  "location": "bangalore",
  "max_count": 10,
  "url": "",
  "message": "brief friendly reply to user"
}
"""


class ChatAgent:
    def __init__(self, bot: NaukriBot) -> None:
        self.bot = bot
        self.history: list[dict[str, str]] = []
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def handle_message(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        command = await self._parse_command(user_message)
        response = await self._execute(command)
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _parse_command(self, message: str) -> ParsedCommand:
        if self._openai:
            try:
                return await self._parse_with_llm(message)
            except Exception:
                pass
        return self._parse_with_rules(message)

    async def _parse_with_llm(self, message: str) -> ParsedCommand:
        response = await self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content or "{}")
        intent = Intent(data.get("intent", "chat"))
        email, password = parse_login_from_text(message)
        return ParsedCommand(
            intent=intent,
            keywords=data.get("keywords", ""),
            location=data.get("location", ""),
            max_count=int(data.get("max_count", 5)),
            url=data.get("url", ""),
            email=email,
            password=password,
            raw_message=data.get("message", message),
        )

    def _parse_with_rules(self, message: str) -> ParsedCommand:
        lower = message.lower().strip()

        if any(w in lower for w in ("help", "what can you", "commands")):
            return ParsedCommand(intent=Intent.HELP, raw_message=message)

        if any(w in lower for w in ("status", "session")):
            return ParsedCommand(intent=Intent.STATUS, raw_message=message)

        if any(w in lower for w in ("start browser", "open browser", "start")):
            return ParsedCommand(intent=Intent.START, raw_message=message)

        if any(w in lower for w in ("stop browser", "close browser", "stop")):
            return ParsedCommand(intent=Intent.STOP, raw_message=message)

        if "login" in lower or "sign in" in lower:
            email, password = parse_login_from_text(message)
            return ParsedCommand(intent=Intent.LOGIN, email=email, password=password, raw_message=message)

        url_match = re.search(r"https?://[^\s]+naukri[^\s]+", message)
        if url_match and any(w in lower for w in ("apply", "application")):
            return ParsedCommand(intent=Intent.APPLY_URL, url=url_match.group(0), raw_message=message)

        location = self._extract_location(lower)
        keywords = self._extract_keywords(lower)
        max_count = self._extract_count(lower)

        if any(w in lower for w in ("apply", "application", "auto apply")):
            return ParsedCommand(
                intent=Intent.APPLY,
                keywords=keywords,
                location=location,
                max_count=max_count,
                raw_message=message,
            )

        if any(w in lower for w in ("search", "find", "look for", "jobs for")):
            return ParsedCommand(
                intent=Intent.SEARCH,
                keywords=keywords,
                location=location,
                max_count=max_count,
                raw_message=message,
            )

        return ParsedCommand(intent=Intent.CHAT, raw_message=message)

    async def _execute(self, command: ParsedCommand) -> str:
        match command.intent:
            case Intent.START:
                return await self.bot.start()

            case Intent.STOP:
                return await self.bot.stop()

            case Intent.LOGIN:
                return await self.bot.login(command.email, command.password)

            case Intent.SEARCH:
                if not command.keywords:
                    return "Please tell me what jobs to search for, e.g. 'search python developer jobs in Bangalore'"
                jobs = await self.bot.search_jobs(
                    command.keywords,
                    command.location,
                    max_results=command.max_count,
                )
                return self._format_jobs(jobs)

            case Intent.APPLY:
                if not command.keywords:
                    return "Please tell me what jobs to apply for, e.g. 'apply to 5 python developer jobs in Pune'"
                results = await self.bot.apply_to_jobs(
                    command.keywords,
                    command.location,
                    max_applications=command.max_count,
                )
                return self._format_apply_results(results)

            case Intent.APPLY_URL:
                if not command.url:
                    return "Please provide a Naukri job URL to apply."
                result = await self.bot.apply_to_url(command.url)
                return self._format_apply_results([result])

            case Intent.STATUS:
                return self._status()

            case Intent.HELP:
                return self._help()

            case _:
                return (
                    "I can help you apply to Naukri jobs. Try:\n"
                    "• **start** — open browser\n"
                    "• **login** — sign in to Naukri\n"
                    "• **search python jobs in Bangalore** — find jobs\n"
                    "• **apply to 5 react developer jobs in Mumbai** — auto-apply\n"
                    "• **status** — check session\n"
                    "• **help** — show all commands"
                )

    def _status(self) -> str:
        active = self.bot.is_active
        logged_in = self.bot.is_logged_in
        return (
            f"**Session Status**\n"
            f"• Browser: {'running' if active else 'stopped'}\n"
            f"• Naukri login: {'yes' if logged_in else 'no'}\n"
            f"• AI mode: {'OpenAI' if self._openai else 'rule-based'}"
        )

    def _help(self) -> str:
        return """**Naukri Job Agent — Commands**

1. **start** — Launch the browser
2. **login** — Sign in (set credentials in `.env` or say `login email@x.com password xyz`)
3. **search** _keywords_ **in** _location_ — Find jobs  
   _Example: search senior python developer jobs in Hyderabad_
4. **apply to** _N_ _keywords_ **jobs in** _location_ — Auto-apply  
   _Example: apply to 3 data scientist jobs in Bangalore_
5. **apply to** _naukri job url_ — Apply to one job
6. **status** — Browser and login status
7. **stop** — Close browser

**Setup:** Copy `.env.example` to `.env`, add your Naukri credentials and optional OpenAI key. Place your resume at `resume.pdf`."""

    def _format_jobs(self, jobs: list[JobListing]) -> str:
        if not jobs:
            return "No jobs found. Try different keywords or location."
        lines = [f"Found **{len(jobs)}** jobs:\n"]
        for i, job in enumerate(jobs, 1):
            easy = " ✓ Easy Apply" if job.has_easy_apply else ""
            lines.append(
                f"{i}. **{job.title}** at {job.company}\n"
                f"   📍 {job.location} | Exp: {job.experience}{easy}\n"
                f"   {job.url}\n"
            )
        return "\n".join(lines)

    def _format_apply_results(self, results: list[ApplyResult]) -> str:
        if not results:
            return "No applications attempted."
        lines = ["**Application Results:**\n"]
        for r in results:
            icon = {"applied": "✅", "skipped": "⏭️", "error": "❌"}.get(r.status, "•")
            if r.job_title:
                lines.append(f"{icon} **{r.job_title}** @ {r.company}: {r.message}")
            else:
                lines.append(f"{icon} {r.message}")
        applied = sum(1 for r in results if r.status == "applied")
        lines.append(f"\n**Total applied: {applied}/{len(results)}**")
        return "\n".join(lines)

    def _extract_location(self, text: str) -> str:
        patterns = [
            r"(?:in|at|near)\s+([a-zA-Z\s]+?)(?:\s+(?:jobs?|for|with|apply)|$)",
            r"location[:\s]+([a-zA-Z\s]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                loc = match.group(1).strip()
                if loc and loc not in ("the", "a", "my"):
                    return loc.title()
        return ""

    def _extract_keywords(self, text: str) -> str:
        cleaned = text
        for phrase in (
            "apply to", "apply for", "auto apply", "search for", "search",
            "find", "look for", "jobs for", "jobs in", "job in",
            "login", "start browser", "help",
        ):
            cleaned = cleaned.replace(phrase, " ")
        cleaned = re.sub(r"\b\d+\b", "", cleaned)
        cleaned = re.sub(r"\b(in|at|near|to|for|the|a|my|jobs?)\b", " ", cleaned, flags=re.I)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "software engineer"

    def _extract_count(self, text: str) -> int:
        match = re.search(r"\b(\d+)\b", text)
        if match:
            return min(int(match.group(1)), 20)
        return 5
