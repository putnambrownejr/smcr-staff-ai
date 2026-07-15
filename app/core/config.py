import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)
SMCR_STAFF_AI_HOME_ENV = "SMCR_STAFF_AI_HOME"


def default_local_state_root() -> Path:
    explicit_home = os.getenv(SMCR_STAFF_AI_HOME_ENV)
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


def default_fitrep_dir() -> Path:
    return default_local_context_dir() / "fitreps"


def default_cadence_dir() -> Path:
    return default_local_context_dir() / "cadences"


def default_chief_capability_audit_dir() -> Path:
    return default_local_context_dir() / "chief_capability_audits"


def default_battle_rhythm_dir() -> Path:
    return default_local_context_dir() / "battle_rhythm"


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


def default_section_memory_dir() -> Path:
    return default_local_context_dir() / "section_memory"


def default_bench_sections_dir() -> Path:
    return default_local_context_dir() / "bench_sections"


def default_user_profile_dir() -> Path:
    return default_local_context_dir() / "user_profiles"


def default_billet_research_dir() -> Path:
    return default_local_context_dir() / "billet_research"


def default_module_packs_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "modules"


def default_history_storage_dir() -> Path:
    return default_local_context_dir() / "history"


def default_active_user_context_dir() -> Path:
    return default_local_context_dir() / "active_user_context"


def default_actions_storage_dir() -> Path:
    return default_local_context_dir() / "actions"


def default_document_updates_dir() -> Path:
    return default_local_context_dir() / "document_updates"


def default_drill_plans_dir() -> Path:
    return default_local_context_dir() / "drill_plans"


def default_opportunities_dir() -> Path:
    return default_local_context_dir() / "opportunities"


def default_source_states_dir() -> Path:
    return default_local_context_dir() / "source_states"


def default_resource_links_dir() -> Path:
    return default_local_context_dir() / "resource_links"


def default_custom_mos_recipes_dir() -> Path:
    return default_local_context_dir() / "custom_mos_recipes"


def default_agent_notes_dir() -> Path:
    return default_local_context_dir() / "agent_notes"


def default_chief_setup_dir() -> Path:
    return default_local_context_dir() / "chief_setup"


def default_external_processing_audits_dir() -> Path:
    return default_local_context_dir() / "external_processing_audits"


def default_projects_dir() -> Path:
    # AGENTS.md ("Saving User Work Products"): user work saves to the repo-root
    # projects/ folder, which is gitignored. The dashboard's Project files
    # tiles open this same path, so save-to-project and open-folder agree.
    return Path(__file__).resolve().parents[2] / "projects"


def default_user_docs_dir() -> Path:
    return default_local_state_root() / "User Docs"


def default_database_url() -> str:
    database_path = default_local_state_root() / "smcr_staff_ai.db"
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    app_name: str = "SMCR Staff AI"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = default_database_url()  # Reserved for future use; not currently wired.
    vector_store_backend: str = "local-stub"  # Reserved for future use; not currently wired.
    local_context_storage_dir: str = str(default_local_context_dir())
    session_handoff_storage_dir: str = str(default_session_handoff_dir())
    product_template_storage_dir: str = str(default_product_template_dir())
    travel_case_storage_dir: str = str(default_travel_case_dir())
    fitrep_storage_dir: str = str(default_fitrep_dir())
    cadence_storage_dir: str = str(default_cadence_dir())
    chief_capability_audit_storage_dir: str = str(default_chief_capability_audit_dir())
    battle_rhythm_storage_dir: str = str(default_battle_rhythm_dir())
    reading_state_storage_dir: str = str(default_reading_state_dir())
    reading_catalog_storage_dir: str = str(default_reading_catalog_dir())
    maradmin_feed_storage_dir: str = str(default_maradmin_feed_dir())
    navy_message_storage_dir: str = str(default_navy_message_dir())
    dod_watch_storage_dir: str = str(default_dod_watch_dir())
    custom_watch_feed_storage_dir: str = str(default_custom_watch_feed_dir())
    section_memory_storage_dir: str = str(default_section_memory_dir())
    bench_sections_storage_dir: str = str(default_bench_sections_dir())
    user_profile_storage_dir: str = str(default_user_profile_dir())
    billet_research_storage_dir: str = str(default_billet_research_dir())
    module_packs_dir: str = str(default_module_packs_dir())
    history_storage_dir: str = str(default_history_storage_dir())
    active_user_context_storage_dir: str = str(default_active_user_context_dir())
    actions_storage_dir: str = str(default_actions_storage_dir())
    document_updates_storage_dir: str = str(default_document_updates_dir())
    drill_plans_storage_dir: str = str(default_drill_plans_dir())
    opportunities_storage_dir: str = str(default_opportunities_dir())
    source_states_storage_dir: str = str(default_source_states_dir())
    resource_links_storage_dir: str = str(default_resource_links_dir())
    custom_mos_recipes_storage_dir: str = str(default_custom_mos_recipes_dir())
    agent_notes_storage_dir: str = str(default_agent_notes_dir())
    chief_setup_storage_dir: str = str(default_chief_setup_dir())
    external_processing_audits_storage_dir: str = str(default_external_processing_audits_dir())
    projects_dir: str = str(default_projects_dir())
    user_docs_dir: str = str(default_user_docs_dir())
    local_api_key: str | None = None
    max_upload_bytes: int = 50_000_000
    public_source_only: bool = True

    # LLM client for scenario-mode template population (optional)
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def configured_storage_dirs(settings: Settings) -> list[Path]:
    return [
        Path(settings.local_context_storage_dir),
        Path(settings.session_handoff_storage_dir),
        Path(settings.product_template_storage_dir),
        Path(settings.travel_case_storage_dir),
        Path(settings.fitrep_storage_dir),
        Path(settings.cadence_storage_dir),
        Path(settings.chief_capability_audit_storage_dir),
        Path(settings.battle_rhythm_storage_dir),
        Path(settings.reading_state_storage_dir),
        Path(settings.reading_catalog_storage_dir),
        Path(settings.maradmin_feed_storage_dir),
        Path(settings.navy_message_storage_dir),
        Path(settings.dod_watch_storage_dir),
        Path(settings.custom_watch_feed_storage_dir),
        Path(settings.section_memory_storage_dir),
        Path(settings.bench_sections_storage_dir),
        Path(settings.user_profile_storage_dir),
        Path(settings.billet_research_storage_dir),
        Path(settings.history_storage_dir),
        Path(settings.active_user_context_storage_dir),
        Path(settings.actions_storage_dir),
        Path(settings.document_updates_storage_dir),
        Path(settings.drill_plans_storage_dir),
        Path(settings.opportunities_storage_dir),
        Path(settings.source_states_storage_dir),
        Path(settings.resource_links_storage_dir),
        Path(settings.custom_mos_recipes_storage_dir),
        Path(settings.agent_notes_storage_dir),
        Path(settings.chief_setup_storage_dir),
        Path(settings.external_processing_audits_storage_dir),
        Path(settings.projects_dir),
        Path(settings.user_docs_dir),
    ]


def ensure_storage_dirs(settings: Settings) -> None:
    for directory in configured_storage_dirs(settings):
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.exception(
                "Could not create storage directory '%s'. Set %s to a writable local state root.",
                directory,
                SMCR_STAFF_AI_HOME_ENV,
            )
            raise


@lru_cache
def get_settings() -> Settings:
    return Settings()
