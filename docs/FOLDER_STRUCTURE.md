# Vidya Copilot — Folder Structure

```
ResumeAgent/
├── vidya_copilot/                 # Main application package
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Environment settings
│   │
│   ├── agents/
│   │   └── orchestrator.py        # Intent routing + agent execution
│   │
│   ├── api/
│   │   ├── deps.py                # API key auth
│   │   └── routes/
│   │       ├── chat.py            # Chat endpoints
│   │       ├── codebase.py        # RAG index/search
│   │       ├── files.py           # File CRUD
│   │       ├── terminal.py        # Shell execution
│   │       ├── memory.py          # Notes, learning, history
│   │       └── health.py          # Health check
│   │
│   ├── llm/
│   │   └── ollama_client.py       # Ollama chat + tool loop
│   │
│   ├── memory/
│   │   ├── database.py            # SQLAlchemy models
│   │   └── store.py               # Memory CRUD API
│   │
│   ├── rag/
│   │   ├── indexer.py             # ChromaDB indexing
│   │   └── retriever.py           # Semantic + symbol search
│   │
│   ├── tools/
│   │   ├── file_tools.py          # Safe file operations
│   │   ├── terminal_tools.py      # Allowlisted commands
│   │   ├── framework_templates.py # Selenium/Playwright/API scaffolds
│   │   └── registry.py            # Tool registry for agent
│   │
│   └── prompts/
│       └── system.py              # Agent system prompts
│
├── frontend/copilot/              # Web chat UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── vscode-extension/              # VS Code / Cursor plugin
│   ├── package.json
│   ├── tsconfig.json
│   └── src/extension.ts
│
├── docs/
│   ├── ARCHITECTURE.md            # System design + diagrams
│   ├── API.md                     # REST API reference
│   ├── DATABASE.md                # SQLite schema
│   ├── ROADMAP.md                 # MVP → Production plan
│   └── FOLDER_STRUCTURE.md      # This file
│
├── backend/                       # Legacy Naukri job agent
├── data/                          # Auto-created (gitignored)
│   ├── vidya_copilot.db           # SQLite memory
│   └── chroma/                    # Vector embeddings
│
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```
