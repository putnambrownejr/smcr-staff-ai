import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def default_local_state_root() -> Path:
    explicit_home = os.getenv("SMCR_STAFF_AI_HOME")
    if explicit_home:
        return Path(explicit_home).expanduser()
    if os.name == "nt":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "smcr-staff-ai"
        return Path.home() / "AppData" / "Local" / "smcr-staff-ai"
    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "smcr-staff-ai"
    return Path.home() / ".local" / "share" / "smcr-staff-ai"


def default_local_context_dir() -> Path:
    return default_local_state_root() / "local_context"


def default_session_handoff_dir() -> Path:
    return default_local_context_dir() / "session_handoffs"


def default_product_template_dir() -> Path:
    return default_local_context_dir() / "product_templates"


def default_travel_case_dir() -> Path:
    return default_local_context_dir() / "travel_cases"


def default_reading_state_dir() -> Path:
    return default_local_context_dir() / "reading_state"


def default_reading_catalog_dir() -> Path:
    return default_local_context_dir() / "reading_catalog"


def default_maradmin_feed_dir() -> Path:
    return default_local_context_dir() / "maradmin_feed"


def default_navy_message_dir() -> Path:
    return default_local_context_dir() / "navy_messages"


def default_dod_watch_dir() -> Path:
    return default_local_context_dir() / "dod_watch"


def default_custom_watch_feed_dir() -> Path:
    return default_local_context_dir() / "custom_watch_feeds"


def default_database_url() -> str:
    database_path = default_local_state_root() / "smcr_staff_ai.db"
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    app_name: str = "SMCR Staff AI"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = default_database_url()
    vector_store_backend: str = "local-stub"
    local_context_storage_dir: str = str(default_local_context_dir())
    session_handoff_storage_dir: str = str(default_session_handoff_dir())
    product_template_storage_dir: str = str(default_product_template_dir())
    travel_case_storage_dir: str = str(default_travel_case_dir())
    reading_state_storage_dir: str = str(default_reading_state_dir())
    reading_catalog_storage_dir: str = str(default_reading_catalog_dir())
    maradmin_feed_storage_dir: str = str(default_maradmin_feed_dir())
    navy_message_storage_dir: str = str(default_navy_message_dir())
    dod_watch_storage_dir: str = str(default_dod_watch_dir())
    custom_watch_feed_storage_dir: str = str(default_custom_watch_feed_dir())
    local_api_key: str | None = None
    max_upload_bytes: int = 50_000_000
    public_source_only: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
