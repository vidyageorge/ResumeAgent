# How to Use Vidya Copilot

Vidya Copilot is your **personal local AI assistant** — a Cursor alternative that runs entirely on your laptop. You chat with it in a browser or from VS Code, and it helps with coding, tests, interviews, learning, and career tasks.

---

## One-Time Setup

### Step 1: Install Ollama (the local AI brain)

1. Download from [https://ollama.com](https://ollama.com)
2. Install and **open the Ollama app** (keep it running in the background)
3. In PowerShell, pull the models:

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

**Windows: `ollama` command not found?** The app is installed but CLI may not be on PATH. Use the full path:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull qwen3:8b
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
```

To fix permanently, add this folder to your PATH:
`C:\Users\<YourUsername>\AppData\Local\Programs\Ollama`

Or restart PowerShell / your PC after installing Ollama — the installer usually adds PATH on reboot.

Keep Ollama running in the background while you use Vidya Copilot.

---

### Step 2: Install Python dependencies

```powershell
cd c:\Users\vidya.g\Documents\GitHub\ResumeAgent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### Step 3: Create your config file

```powershell
copy .env.example .env
```

Edit `.env` and set at least these:

| Setting | What to put |
|--------|-------------|
| `WORKSPACE_ROOT` | Folder where your projects live, e.g. `c:\Users\vidya.g\Documents\GitHub` |
| `API_KEY` | Any secret string you choose, e.g. `my-local-key-123` |
| `OLLAMA_MODEL` | `qwen3:8b` (default is fine) |

The copilot can only read/write files **inside** `WORKSPACE_ROOT`.

---

### Step 4: Start Vidya Copilot

```powershell
cd c:\Users\vidya.g\Documents\GitHub\ResumeAgent
.venv\Scripts\activate
python run.py
```

You should see the server start on port 8000.

---

## Daily Usage — 3 Ways to Talk to It

### Option A: Web Chat (easiest)

1. Open **http://127.0.0.1:8000** in your browser
2. Pick an agent on the left (or leave **Auto**)
3. Type your question and press **Send**

**First time with a project:** click **Index Workspace** so it can search your code.

---

### Option B: VS Code / Cursor Extension

```powershell
cd c:\Users\vidya.g\Documents\GitHub\ResumeAgent\vscode-extension
npm install
npm run compile
```

Then in VS Code:

1. Open the `vscode-extension` folder
2. Press **F5** to run the extension
3. Use **`Ctrl+Shift+V`** to open chat

Commands in the Command Palette (`Ctrl+Shift+P`):

| Command | What it does |
|---------|--------------|
| Vidya Copilot: Open Chat | Ask anything |
| Vidya Copilot: Ask About Selection | Select code, then ask |
| Vidya Copilot: Review Current File | Review open file |
| Vidya Copilot: Index Project | Index workspace for code search |

In VS Code settings, set:

- `vidyaCopilot.serverUrl` → `http://127.0.0.1:8000`
- `vidyaCopilot.apiKey` → same value as `API_KEY` in `.env`

---

### Option C: API (PyCharm, IntelliJ, scripts)

```http
POST http://127.0.0.1:8000/api/chat
X-API-Key: your-api-key-from-env
Content-Type: application/json

{
  "message": "Create a Playwright Python framework with POM",
  "agent": "coding"
}
```

Interactive API docs: **http://127.0.0.1:8000/docs**

See [API.md](API.md) for the full reference.

---

## Copilot vs Agent — What's the Difference?

| Term | Meaning |
|------|---------|
| **Vidya Copilot** | The whole system — UI, server, memory, tools, Ollama |
| **Agent** | A specialist inside the copilot for a specific job |

**One copilot, many agents.** The orchestrator picks the right agent for your message (or you can pick one manually).

```
You → Vidya Copilot → Orchestrator → Agent → Tools + Memory → Reply
```

---

## The 6 Agents — When to Use Each

| Agent | Use for |
|-------|---------|
| **Auto** | Let it pick the right agent |
| **Coding** | Frameworks, tests, POM, locators, bug fixes, code review |
| **Interview** | Mock interviews (Playwright, Selenium, Python, AI) |
| **Learning** | RAG, embeddings, agentic AI, quizzes |
| **Career** | Resume, LinkedIn, cover letters |
| **Productivity** | Notes, goals, remembering preferences |

You can also say things like "start a Playwright interview" and **Auto** will route correctly.

---

## Example Prompts

### Coding

```
Create a Selenium Python framework using Pytest, POM, Allure in folder my-selenium-fw

Where is LoginPage used?

Review my test framework and suggest improvements

Fix the failing test in tests/test_login.py
```

### Project understanding (index first)

```
Index my project, then find all API clients

Show duplicate code patterns in my framework
```

### Interview

```
Start a mid-level Playwright interview

Quiz me on Python pytest fixtures
```

### Learning

```
Explain RAG in simple terms with a QA example

Create a 4-week learning plan for Agentic AI
```

### Career

```
Review my resume for Senior QA Automation roles

Write a cover letter for a Playwright automation job
```

### Memory

```
Remember that I prefer Playwright over Selenium for new projects
```

---

## Typical Workflow

1. Start **Ollama**
2. Run **`python run.py`**
3. Open the **web UI** at http://127.0.0.1:8000
4. Click **Index Workspace** (once per project)
5. Ask questions or give tasks
6. For coding tasks, it may create/edit files and run `pytest` under your workspace

---

## Health Check

Open: **http://127.0.0.1:8000/health**

You want:

- `"status": "ok"`
- Ollama `"model_available": true`

If Ollama is offline, start the Ollama app and run `ollama pull qwen3:8b` again.

---

## Troubleshooting

| Problem | Fix |
|--------|-----|
| "Ollama offline" | Start Ollama app; run `ollama list` |
| Slow replies | Normal on CPU; GPU helps; use `qwen3:8b` not larger models |
| "Invalid API key" | Match `X-API-Key` / web UI key with `.env` `API_KEY` |
| Can't find code | Click **Index Workspace** or call `POST /api/codebase/index` |
| File not found | Check path is under `WORKSPACE_ROOT` in `.env` |
| Command blocked | Only allowlisted commands (pytest, git, playwright, etc.) |

---

## Quick Reference

| What | Where |
|------|--------|
| Web UI | http://127.0.0.1:8000 |
| API docs | http://127.0.0.1:8000/docs |
| Start server | `python run.py` |
| Config | `.env` |
| Chat history & memory | `data/vidya_copilot.db` |
| Code index | `data/chroma/` |

---

## Minimum Steps to Use It Today

1. Ollama running with `qwen3:8b`
2. `.env` configured
3. `python run.py`
4. Browser → http://127.0.0.1:8000 → chat

---

## Related Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [API.md](API.md) — REST API reference
- [ROADMAP.md](ROADMAP.md) — Future features
- [DATABASE.md](DATABASE.md) — Memory schema
