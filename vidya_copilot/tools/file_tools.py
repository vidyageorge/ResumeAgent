"""Safe file operations within workspace boundary."""

from __future__ import annotations

import shutil
from pathlib import Path

from vidya_copilot.config import settings


class FileTools:
    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = (workspace or settings.workspace_path).resolve()

    def _resolve_safe(self, relative_path: str) -> Path:
        target = (self.workspace / relative_path).resolve()
        if not str(target).startswith(str(self.workspace)):
            raise PermissionError(f"Path outside workspace: {relative_path}")
        return target

    def read_file(self, path: str) -> str:
        target = self._resolve_safe(path)
        if not target.exists():
            return f"File not found: {path}"
        return target.read_text(encoding="utf-8", errors="ignore")

    def write_file(self, path: str, content: str) -> str:
        target = self._resolve_safe(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Written: {path} ({len(content)} bytes)"

    def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        target = self._resolve_safe(path)
        if not target.exists():
            return f"File not found: {path}"
        content = target.read_text(encoding="utf-8")
        if old_text not in content:
            return f"Text not found in {path}"
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited: {path}"

    def delete_file(self, path: str) -> str:
        target = self._resolve_safe(path)
        if not target.exists():
            return f"File not found: {path}"
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return f"Deleted: {path}"

    def rename_file(self, old_path: str, new_path: str) -> str:
        src = self._resolve_safe(old_path)
        dst = self._resolve_safe(new_path)
        if not src.exists():
            return f"File not found: {old_path}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"Renamed: {old_path} → {new_path}"

    def list_directory(self, path: str = ".") -> str:
        target = self._resolve_safe(path)
        if not target.exists():
            return f"Directory not found: {path}"
        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = [f"{'[DIR]' if e.is_dir() else '[FILE]'} {e.name}" for e in entries[:100]]
        return "\n".join(lines) or "(empty)"

    def create_directory(self, path: str) -> str:
        target = self._resolve_safe(path)
        target.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {path}"

    def generate_project_structure(self, base_path: str, structure: dict) -> str:
        """Create nested project structure from dict like {'tests': {'test_login.py': ''}}."""
        created: list[str] = []

        def walk(current: Path, tree: dict) -> None:
            for name, value in tree.items():
                item = current / name
                if isinstance(value, dict):
                    item.mkdir(parents=True, exist_ok=True)
                    created.append(str(item.relative_to(self.workspace)))
                    walk(item, value)
                else:
                    item.parent.mkdir(parents=True, exist_ok=True)
                    item.write_text(value if isinstance(value, str) else "", encoding="utf-8")
                    created.append(str(item.relative_to(self.workspace)))

        root = self._resolve_safe(base_path)
        root.mkdir(parents=True, exist_ok=True)
        walk(root, structure)
        return f"Created {len(created)} items under {base_path}"
