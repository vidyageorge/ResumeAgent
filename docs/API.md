# Vidya Copilot — API Design

Base URL: `http://127.0.0.1:8000`

All endpoints (except `/health` and `/`) require header:
```
X-API-Key: your-api-key
```

Interactive docs: `http://127.0.0.1:8000/docs`

---

## Health

### `GET /health`
```json
{
  "status": "ok",
  "service": "Vidya Copilot",
  "version": "0.1.0",
  "workspace": "C:\\Users\\vidya.g\\Documents\\GitHub",
  "ollama": {
    "status": "ok",
    "models": ["qwen3:8b", "nomic-embed-text"],
    "configured_model": "qwen3:8b",
    "model_available": true
  }
}
```

---

## Chat

### `POST /api/chat`
```json
{
  "message": "Create a Selenium Python framework with Pytest, POM, Allure",
  "session_id": "optional-uuid",
  "agent": "coding"
}
```

Response:
```json
{
  "reply": "...",
  "session_id": "abc-123",
  "agent": "coding"
}
```

### `GET /api/chat/agents`
Lists available agents.

### `WS /ws`
WebSocket chat. Send:
```json
{"message": "...", "session_id": "...", "agent": "coding"}
```

---

## Codebase (RAG)

### `POST /api/codebase/index`
```json
{"project_path": "C:\\path\\to\\project"}
```

### `POST /api/codebase/search`
```json
{"query": "LoginPage", "top_k": 8}
```

### `POST /api/codebase/ask`
Returns formatted RAG context for a question.

### `POST /api/codebase/symbol`
```json
{"symbol": "LoginPage", "project_path": null}
```

---

## Files

| Method | Path | Body |
|--------|------|------|
| POST | `/api/files/read` | `{"path": "project/tests/test_login.py"}` |
| POST | `/api/files/write` | `{"path": "...", "content": "..."}` |
| POST | `/api/files/edit` | `{"path": "...", "old_text": "...", "new_text": "..."}` |
| POST | `/api/files/delete` | `{"path": "..."}` |
| POST | `/api/files/rename` | `{"old_path": "...", "new_path": "..."}` |
| GET | `/api/files/list?path=.` | — |

---

## Terminal

### `POST /api/terminal/run`
```json
{"command": "pytest tests/ -v", "cwd": "my-project"}
```

### `POST /api/terminal/pytest`
```json
{"path": "tests/", "extra_args": "-v --tb=short"}
```

### `POST /api/terminal/playwright`
```json
{"path": "tests/", "extra_args": ""}
```

### `GET /api/terminal/git/status`

---

## Memory

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/memory` | List memory entries |
| POST | `/api/memory/set` | `{"category": "...", "key": "...", "value": "..."}` |
| GET | `/api/memory/history/{session_id}` | Chat history |
| POST | `/api/memory/notes` | Add note |
| GET | `/api/memory/notes` | List notes |
| POST | `/api/memory/learning` | Update learning progress |
| GET | `/api/memory/learning` | Get learning progress |
| GET | `/api/memory/interviews` | List interview sessions |
