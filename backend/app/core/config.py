from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./interview.db"
    vector_db_path: str = "./data/vector_index.pkl"
    embedding_model: str = "tfidf-local"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    cors_origins: str = "http://localhost:5173"
    upload_max_bytes: int = 5_000_000
    questions_per_interview: int = 5
    auto_create_schema: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ensure_dirs(self) -> None:
        Path(self.vector_db_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
