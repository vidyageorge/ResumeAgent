# Vidya Copilot — Database Design

SQLite database at `./data/vidya_copilot.db`

## Tables

### `conversations`
Stores all chat messages for session continuity.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | VARCHAR(64) | Chat session UUID |
| role | VARCHAR(16) | `user` or `assistant` |
| content | TEXT | Message content |
| agent_type | VARCHAR(32) | Agent that handled the message |
| created_at | DATETIME | UTC timestamp |

### `memory_entries`
Long-term memory for preferences, tech stack, notes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| category | VARCHAR(64) | e.g. `tech_stack`, `preferences`, `user_notes` |
| key | VARCHAR(128) | Memory key |
| value | TEXT | JSON or text value |
| created_at | DATETIME | Created |
| updated_at | DATETIME | Last updated |

**Seeded defaults:**
- `tech_stack/profile` — Playwright, Selenium, Python, TypeScript, PostgreSQL
- `preferences/profile` — pytest, Allure, POM, Jenkins, GitHub Actions

### `notes`
Personal knowledge notes.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| title | VARCHAR(256) | Note title |
| content | TEXT | Note body |
| tags | VARCHAR(512) | Comma-separated tags |
| created_at | DATETIME | Created |

### `learning_progress`
AI learning journey tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| topic | VARCHAR(128) UNIQUE | e.g. `RAG`, `Agentic AI` |
| level | VARCHAR(32) | beginner / intermediate / advanced |
| progress_pct | FLOAT | 0-100 |
| notes | TEXT | Learning notes |
| updated_at | DATETIME | Last updated |

### `interview_sessions`
Mock interview history with scores.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| topic | VARCHAR(64) | Playwright, Selenium, Python, AI |
| difficulty | VARCHAR(32) | junior / mid / senior |
| score | FLOAT | 0-10 |
| feedback | TEXT | Detailed feedback |
| transcript | TEXT | Full Q&A transcript |
| created_at | DATETIME | Session date |

### `indexed_projects`
Tracks which projects have been indexed for RAG.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| project_path | VARCHAR(512) UNIQUE | Absolute project path |
| file_count | INTEGER | Files indexed |
| last_indexed_at | DATETIME | Last index time |

## Vector Store (ChromaDB)

Separate from SQLite, stored at `./data/chroma/`.

| Field | Description |
|-------|-------------|
| collection | `vidya_codebase` |
| documents | Code chunks (1000 chars, 200 overlap) |
| metadata | `source`, `project`, `chunk`, `language` |
| embeddings | `nomic-embed-text` via Ollama |

## Data Flow

```
User chat → conversations table
"Remember X" → memory_entries table
Index project → indexed_projects + ChromaDB
Interview → interview_sessions
Learning update → learning_progress
```
