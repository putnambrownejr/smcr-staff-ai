import logging
import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    actions,
    admin,
    agent_notes,
    agents,
    analysis,
    battle_rhythm,
    bench_sections,
    billets,
    cadences,
    calendar,
    career,
    career_opportunities,
    civil_networks,
    chief,
    chief_setup,
    connectors,
    context,
    custom_mos_recipes,
    custom_watch_feeds,
    dashboard,
    demo,
    documents,
    family_readiness,
    fitness,
    fitreps,
    git_ops,
    handoffs,
    health,
    history,
    maradmins,
    message_watch,
    modules,
    opportunities,
    org,
    personal_documents,
    personnel,
    planning,
    privacy,
    product_templates,
    prompt_packs,
    reading,
    reading_state,
    resource_links,
    section_memory,
    sharing,
    skills,
    social,
    source_updates,
    staff,
    staff_products,
    training,
    travel_cases,
    user_context,
    user_docs,
    user_profile,
)
from app.core.config import Settings, ensure_storage_dirs, get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    # Configure logging before startup checks so path failures include clear context.
    configure_logging()
    settings = get_settings()
    ensure_storage_dirs(settings)
    _warn_if_auth_disabled(settings)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "UNCLASSIFIED prototype toolkit for SMCR staff workflows. "
            "Outputs are advisory drafts requiring human review."
        ),
    )
    app.include_router(health.router)
    app.include_router(history.router)
    app.include_router(actions.router)
    app.include_router(admin.router)
    app.include_router(analysis.router)
    app.include_router(agents.router)
    app.include_router(agent_notes.router)
    app.include_router(battle_rhythm.router)
    app.include_router(billets.router)
    app.include_router(career.router)
    app.include_router(career_opportunities.router)
    app.include_router(civil_networks.router)
    app.include_router(context.router)
    app.include_router(custom_mos_recipes.router)
    app.include_router(custom_watch_feeds.router)
    app.include_router(demo.router)
    app.include_router(connectors.router)
    app.include_router(documents.router)
    app.include_router(fitreps.router)
    app.include_router(fitness.router)
    app.include_router(family_readiness.router)
    app.include_router(handoffs.router)
    app.include_router(calendar.router)
    app.include_router(cadences.router)
    app.include_router(chief.router)
    app.include_router(chief_setup.router)
    app.include_router(dashboard.router)
    app.include_router(org.router)
    app.include_router(opportunities.router)
    app.include_router(planning.router)
    app.include_router(personal_documents.router)
    app.include_router(personnel.router)
    app.include_router(product_templates.router)
    app.include_router(privacy.router)
    app.include_router(reading.router)
    app.include_router(reading_state.router)
    app.include_router(bench_sections.router)
    app.include_router(resource_links.router)
    app.include_router(user_docs.router)
    app.include_router(user_profile.router)
    app.include_router(section_memory.router)
    app.include_router(maradmins.router)
    app.include_router(message_watch.router)
    app.include_router(modules.router)
    app.include_router(git_ops.router)
    app.include_router(social.router)
    app.include_router(staff.router)
    app.include_router(staff_products.router)
    app.include_router(sharing.router)
    app.include_router(skills.router)
    app.include_router(prompt_packs.router)
    app.include_router(source_updates.router)
    app.include_router(training.router)
    app.include_router(travel_cases.router)
    app.include_router(user_context.router)
    # Use absolute path so the dashboard serves correctly regardless of
    # the working directory the server is launched from (fixes #21 extension)
    _static_dir = Path(__file__).resolve().parent / "static"
    # Python's mimetypes module doesn't know .webmanifest; without this, the
    # PWA manifest serves as application/octet-stream on machines whose OS
    # doesn't register the type (StaticFiles uses mimetypes.guess_type).
    mimetypes.add_type("application/manifest+json", ".webmanifest")
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
    return app


def _warn_if_auth_disabled(settings: Settings) -> None:
    """Log a prominent warning when no local API key is configured (issue #20).

    When ``local_api_key`` is unset, ``LocalApiKeyDependency`` is a no-op and every
    personal/write route is reachable without a key. That is a reasonable default
    for a private single-user machine, but it should never be silent — a user who
    exposes the port (LAN, tunnel, container) needs to know the gate is open.
    """
    if settings.local_api_key is None:
        logging.getLogger("smcr_staff_ai").warning(
            "LOCAL_API_KEY is not set - all personal and write-capable routes are "
            "reachable WITHOUT authentication. This is fine for a private local "
            "machine, but set LOCAL_API_KEY before exposing this server to a "
            "network, tunnel, or shared host."
        )


app = create_app()
