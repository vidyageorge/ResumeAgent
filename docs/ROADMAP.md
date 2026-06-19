# Vidya Copilot — Implementation Roadmap

## Phase 1: MVP (v0.1) — ✅ Current

**Goal:** Working local assistant you can use today.

| Task | Status |
|------|--------|
| FastAPI server with REST + WebSocket | ✅ |
| Ollama integration (Qwen3) | ✅ |
| Agent orchestrator with 6 agents | ✅ |
| Tool calling (files, terminal, RAG, scaffold) | ✅ |
| ChromaDB RAG indexing | ✅ |
| SQLite long-term memory | ✅ |
| Web chat UI | ✅ |
| VS Code extension scaffold | ✅ |
| Framework templates (Selenium, Playwright, API) | ✅ |
| API key authentication | ✅ |
| Documentation | ✅ |

**Setup time:** ~30 minutes

---

## Phase 2: Advanced (v0.5) — 2-4 weeks

| Task | Priority |
|------|----------|
| Streaming LLM responses (SSE) | High |
| JetBrains plugin (PyCharm/IntelliJ) | High |
| Interview scoring persistence + analytics | High |
| Multi-project workspace switching | Medium |
| Git diff awareness in context | Medium |
| Test failure analysis agent | High |
| Locator generator from HTML snapshots | Medium |
| PostgreSQL test data management tools | Medium |
| Resume parser + job matcher | Medium |
| Conversation export/import | Low |

---

## Phase 3: Production (v1.0) — 2-3 months

| Task | Priority |
|------|----------|
| Encrypted SQLite (SQLCipher) | High |
| Model routing (Qwen3 for code, smaller model for chat) | High |
| Plugin marketplace (custom tools) | Medium |
| Team mode (shared memory, private keys) | Medium |
| CI/CD integration (GitHub Actions bot) | High |
| Docker deployment option | Medium |
| Offline embedding cache | Medium |
| Usage analytics dashboard | Low |
| Voice input/output | Low |
| Mobile companion app | Low |

---

## Step-by-Step Setup (MVP)

### 1. Install Ollama
```powershell
# Download from https://ollama.com
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 2. Install Python dependencies
```powershell
cd c:\Users\vidya.g\Documents\GitHub\ResumeAgent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure
```powershell
copy .env.example .env
# Edit .env: set WORKSPACE_ROOT, API_KEY
```

### 4. Start Vidya Copilot
```powershell
python -m vidya_copilot.main
```

### 5. Open Web UI
http://127.0.0.1:8000

### 6. Index your projects
Click "Index Workspace" or:
```powershell
curl -X POST http://127.0.0.1:8000/api/codebase/index `
  -H "X-API-Key: dev-local-key" `
  -H "Content-Type: application/json" `
  -d "{}"
```

### 7. Install VS Code Extension
```powershell
cd vscode-extension
npm install
npm run compile
# In VS Code: Extensions → Install from VSIX or F5 to debug
```

---

## Example Workflows

### Create Selenium Framework
```
Agent: Coding
Message: "Create a Selenium Python framework using Pytest, POM, Allure, Jenkins and GitHub Actions in folder selenium-framework"
```

### Code Review
```
Agent: Coding
Message: "Review my framework and suggest improvements"
(then index project first)
```

### Mock Interview
```
Agent: Interview
Message: "Start a mid-level Playwright interview"
```

### Learn RAG
```
Agent: Learning
Message: "Explain RAG with examples from my automation background"
```

### Resume Review
```
Agent: Career
Message: "Review my resume for Senior QA Automation roles focusing on Playwright and AI"
```

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16 GB | 32 GB |
| GPU | Not required | NVIDIA 8GB+ VRAM for faster Qwen3 |
| Disk | 10 GB free | 20 GB (models + indexes) |
| CPU | 4 cores | 8+ cores |

Qwen3 8B runs on CPU but is slower (~5-15 tokens/sec). GPU significantly improves experience.
