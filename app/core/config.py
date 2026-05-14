from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SMCR Staff AI"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = "sqlite:///./smcr_staff_ai.db"
    vector_store_backend: str = "local-stub"
    local_context_storage_dir: str = "data/local_context"
    session_handoff_storage_dir: str = "data/local_context/session_handoffs"
    local_api_key: str | None = None
    max_upload_bytes: int = 10_000_000
    public_source_only: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
