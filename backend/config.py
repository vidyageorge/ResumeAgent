from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    naukri_email: str = ""
    naukri_password: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    headless: bool = False
    resume_path: str = "./resume.pdf"

    @property
    def resume_file(self) -> Path:
        return Path(self.resume_path)


settings = Settings()
