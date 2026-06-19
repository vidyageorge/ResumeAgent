"""High-level memory store for conversations, preferences, and notes."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session, sessionmaker

from vidya_copilot.memory.database import (
    Conversation,
    IndexedProject,
    InterviewSession,
    LearningProgress,
    MemoryEntry,
    Note,
)


class MemoryStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        defaults = {
            "tech_stack": {
                "primary": ["Playwright", "Selenium", "Python", "TypeScript", "API Testing"],
                "database": ["PostgreSQL"],
                "learning": ["AI Engineering", "RAG", "Agentic AI", "LLM Applications"],
            },
            "preferences": {
                "test_framework": "pytest",
                "reporting": "Allure",
                "ci": ["Jenkins", "GitHub Actions"],
                "pattern": "Page Object Model",
            },
        }
        with self._session_factory() as session:
            for category, data in defaults.items():
                existing = (
                    session.query(MemoryEntry)
                    .filter_by(category=category, key="profile")
                    .first()
                )
                if not existing:
                    session.add(
                        MemoryEntry(
                            category=category,
                            key="profile",
                            value=json.dumps(data, indent=2),
                        )
                    )
            session.commit()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_type: str = "general",
    ) -> None:
        with self._session_factory() as session:
            session.add(
                Conversation(
                    session_id=session_id,
                    role=role,
                    content=content,
                    agent_type=agent_type,
                )
            )
            session.commit()

    def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, str]]:
        with self._session_factory() as session:
            rows = (
                session.query(Conversation)
                .filter_by(session_id=session_id)
                .order_by(Conversation.id.desc())
                .limit(limit)
                .all()
            )
            return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    def set_memory(self, category: str, key: str, value: str) -> None:
        with self._session_factory() as session:
            entry = (
                session.query(MemoryEntry).filter_by(category=category, key=key).first()
            )
            if entry:
                entry.value = value
                entry.updated_at = datetime.now(timezone.utc)
            else:
                session.add(MemoryEntry(category=category, key=key, value=value))
            session.commit()

    def get_memory(self, category: str, key: str) -> str | None:
        with self._session_factory() as session:
            entry = (
                session.query(MemoryEntry).filter_by(category=category, key=key).first()
            )
            return entry.value if entry else None

    def list_memory(self, category: str | None = None) -> list[dict[str, str]]:
        with self._session_factory() as session:
            query = session.query(MemoryEntry)
            if category:
                query = query.filter_by(category=category)
            return [
                {"category": e.category, "key": e.key, "value": e.value}
                for e in query.all()
            ]

    def add_note(self, title: str, content: str, tags: str = "") -> int:
        with self._session_factory() as session:
            note = Note(title=title, content=content, tags=tags)
            session.add(note)
            session.commit()
            return note.id

    def list_notes(self, tag: str | None = None) -> list[dict]:
        with self._session_factory() as session:
            notes = session.query(Note).order_by(Note.id.desc()).all()
            if tag:
                notes = [n for n in notes if tag in n.tags]
            return [
                {"id": n.id, "title": n.title, "content": n.content, "tags": n.tags}
                for n in notes
            ]

    def update_learning(self, topic: str, level: str, progress_pct: float, notes: str = "") -> None:
        with self._session_factory() as session:
            row = session.query(LearningProgress).filter_by(topic=topic).first()
            if row:
                row.level = level
                row.progress_pct = progress_pct
                row.notes = notes
                row.updated_at = datetime.now(timezone.utc)
            else:
                session.add(
                    LearningProgress(
                        topic=topic,
                        level=level,
                        progress_pct=progress_pct,
                        notes=notes,
                    )
                )
            session.commit()

    def get_learning_progress(self) -> list[dict]:
        with self._session_factory() as session:
            rows = session.query(LearningProgress).all()
            return [
                {
                    "topic": r.topic,
                    "level": r.level,
                    "progress_pct": r.progress_pct,
                    "notes": r.notes,
                }
                for r in rows
            ]

    def save_interview(
        self,
        topic: str,
        difficulty: str,
        score: float,
        feedback: str,
        transcript: str,
    ) -> int:
        with self._session_factory() as session:
            row = InterviewSession(
                topic=topic,
                difficulty=difficulty,
                score=score,
                feedback=feedback,
                transcript=transcript,
            )
            session.add(row)
            session.commit()
            return row.id

    def list_interviews(self, limit: int = 10) -> list[dict]:
        with self._session_factory() as session:
            rows = (
                session.query(InterviewSession)
                .order_by(InterviewSession.id.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "topic": r.topic,
                    "difficulty": r.difficulty,
                    "score": r.score,
                    "feedback": r.feedback,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]

    def record_indexed_project(self, project_path: str, file_count: int) -> None:
        with self._session_factory() as session:
            row = session.query(IndexedProject).filter_by(project_path=project_path).first()
            if row:
                row.file_count = file_count
                row.last_indexed_at = datetime.now(timezone.utc)
            else:
                session.add(
                    IndexedProject(project_path=project_path, file_count=file_count)
                )
            session.commit()

    def get_context_for_prompt(self) -> str:
        memories = self.list_memory()
        learning = self.get_learning_progress()
        parts = ["## User Memory"]
        for m in memories:
            parts.append(f"- **{m['category']}/{m['key']}**: {m['value']}")
        if learning:
            parts.append("\n## Learning Progress")
            for item in learning:
                parts.append(
                    f"- {item['topic']}: {item['level']} ({item['progress_pct']}%)"
                )
        return "\n".join(parts)
