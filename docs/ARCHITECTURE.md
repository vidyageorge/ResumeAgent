# Vidya Copilot — Architecture

## System Overview

Vidya Copilot is a **local-first personal AI assistant** that replaces cloud coding assistants like Cursor. It runs entirely on your laptop using Ollama (Qwen3) and connects to any IDE via REST API and VS Code extension.

```mermaid
flowchart TB
    subgraph IDEs["IDE Layer"]
        VSCode[VS Code Extension]
        PyCharm[PyCharm / IntelliJ<br/>via REST API]
        Cursor[Cursor / Any Editor<br/>via HTTP]
        WebUI[Web Chat UI]
    end

    subgraph API["API Layer — FastAPI"]
        REST[REST Endpoints]
        WS[WebSocket /ws]
        Auth[API Key Auth]
    end

    subgraph Agent["Agent Layer"]
        Orch[Agent Orchestrator]
        Coding[Coding Agent]
        Interview[Interview Coach]
        Learning[AI Learning Coach]
        Career[Career Coach]
        Productivity[Productivity Agent]
    end

    subgraph Tools["Tool Layer"]
        Files[File Tools]
        Terminal[Terminal Tools]
        RAGSearch[Code Search]
        Scaffold[Framework Scaffolder]
    end

    subgraph Intelligence["Intelligence Layer"]
        Ollama[Ollama — Qwen3]
        Embed[Ollama Embeddings]
    end

    subgraph Storage["Storage Layer"]
        SQLite[(SQLite Memory)]
        Chroma[(ChromaDB Vectors)]
        Workspace[Workspace Files]
    end

    VSCode --> REST
    PyCharm --> REST
    Cursor --> REST
    WebUI --> WS
    WebUI --> REST

    REST --> Auth --> Orch
    WS --> Orch

    Orch --> Coding
    Orch --> Interview
    Orch --> Learning
    Orch --> Career
    Orch --> Productivity

    Coding --> Tools
    Orch --> Tools

    Tools --> Files --> Workspace
    Tools --> Terminal --> Workspace
    Tools --> RAGSearch --> Chroma
    Tools --> Scaffold --> Workspace

    Orch --> Ollama
    RAGSearch --> Embed
    Orch --> SQLite
    Chroma --> Embed
```

## Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant Orch as Orchestrator
    participant LLM as Ollama Qwen3
    participant Tools
    participant Memory as SQLite
    participant RAG as ChromaDB

    User->>API: POST /api/chat
    API->>Orch: message + session_id
    Orch->>Orch: detect agent intent
    Orch->>Memory: load history + preferences
    Orch->>LLM: system prompt + memory + message

    loop Tool Calling (max 10 iterations)
        LLM->>Orch: tool call JSON
        Orch->>Tools: execute tool
        Tools->>RAG: search_codebase (if needed)
        Tools-->>Orch: tool result
        Orch->>LLM: tool result
    end

    LLM-->>Orch: final response
    Orch->>Memory: save conversation
    Orch-->>API: reply + agent + session_id
    API-->>User: response
```

## Tool Calling Architecture

```mermaid
flowchart LR
    LLM[Ollama LLM] -->|JSON tool call| Parser[Tool Parser]
    Parser --> Registry[Tool Registry]
    Registry --> FT[File Tools]
    Registry --> TT[Terminal Tools]
    Registry --> CS[Code Search]
    Registry --> FS[Framework Scaffold]
    FT --> Result[Tool Result]
    TT --> Result
    CS --> Result
    FS --> Result
    Result --> LLM
```

### Available Tools

| Tool | Purpose |
|------|---------|
| `read_file` | Read workspace files |
| `write_file` | Create/overwrite files |
| `edit_file` | Search-replace in files |
| `delete_file` | Delete files/directories |
| `rename_file` | Rename/move files |
| `list_directory` | List directory contents |
| `run_command` | Execute allowlisted shell commands |
| `run_pytest` | Run pytest |
| `run_playwright` | Run Playwright tests |
| `git_status` | Git status |
| `search_codebase` | Semantic RAG search |
| `find_symbol` | Grep symbol usage |
| `index_project` | Index project into ChromaDB |
| `scaffold_framework` | Generate Selenium/Playwright/API framework |

## RAG Pipeline

```mermaid
flowchart LR
    Project[Project Files] --> Scanner[File Scanner]
    Scanner --> Splitter[Text Splitter<br/>1000 chars / 200 overlap]
    Splitter --> Embed[Ollama Embeddings<br/>nomic-embed-text]
    Embed --> Chroma[(ChromaDB)]
    Query[User Query] --> Embed
    Embed --> Search[Similarity Search top-k]
    Chroma --> Search
    Search --> Context[Context for LLM]
```

## Memory System

```mermaid
erDiagram
    conversations {
        int id PK
        string session_id
        string role
        text content
        string agent_type
        datetime created_at
    }
    memory_entries {
        int id PK
        string category
        string key
        text value
        datetime updated_at
    }
    notes {
        int id PK
        string title
        text content
        string tags
    }
    learning_progress {
        int id PK
        string topic
        string level
        float progress_pct
        text notes
    }
    interview_sessions {
        int id PK
        string topic
        string difficulty
        float score
        text feedback
        text transcript
    }
    indexed_projects {
        int id PK
        string project_path
        int file_count
        datetime last_indexed_at
    }
```

## IDE Integration

| IDE | Integration Method |
|-----|-------------------|
| VS Code / Cursor | VS Code extension (`Ctrl+Shift+V`) |
| PyCharm / IntelliJ | HTTP Client / Custom plugin calling REST API |
| Any editor | Web UI at `http://127.0.0.1:8000` |
| CLI | `curl` to `/api/chat` |

### PyCharm Integration (HTTP Client)

```http
POST http://127.0.0.1:8000/api/chat
X-API-Key: your-key
Content-Type: application/json

{
  "message": "Review this test class",
  "agent": "coding"
}
```

## Security Considerations

| Risk | Mitigation |
|------|-----------|
| Path traversal | All file ops restricted to `WORKSPACE_ROOT` |
| Dangerous commands | Command allowlist + blocklist |
| Unauthorized access | API key required on all endpoints |
| Data leakage | Everything runs locally — no cloud by default |
| Credential exposure | `.env` gitignored, never logged |
| Command timeout | 120s max execution time |
| Large file reads | 500KB file size limit for indexing |

## Version Roadmap

| Version | Scope |
|---------|-------|
| **MVP (v0.1)** | Chat, coding agent, file/terminal tools, RAG, memory, web UI, VS Code extension |
| **Advanced (v0.5)** | Multi-project indexing, streaming responses, JetBrains plugin, interview scoring persistence |
| **Production (v1.0)** | Plugin marketplace, team mode, encrypted memory, model routing, CI integration |

See [ROADMAP.md](ROADMAP.md) for the full implementation plan.
