from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8000
    api_key: str = "dev-local-key"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    ollama_embed_model: str = "nomic-embed-text"

    workspace_root: str = str(Path.home() / "Documents")
    data_dir: str = "./data"
    chroma_dir: str = "./data/chroma"
    sqlite_path: str = "./data/vidya_copilot.db"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    rag_top_k: int = 8

    max_tool_iterations: int = 10
    command_timeout_seconds: int = 120

    user_name: str = "Vidya"
    user_role: str = "QA Automation Engineer"

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_root).resolve()

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_dir).resolve()

    @property
    def db_path(self) -> Path:
        return Path(self.sqlite_path).resolve()


settings = Settings()
