from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    actions,
    admin,
    agents,
    analysis,
    battle_rhythm,
    billets,
    calendar,
    career,
    chief,
    connectors,
    context,
    custom_watch_feeds,
    dashboard,
    demo,
    documents,
    handoffs,
    health,
    history,
    maradmins,
    message_watch,
    opportunities,
    org,
    personal_documents,
    personnel,
    planning,
    privacy,
    product_templates,
    reading,
    reading_state,
    section_memory,
    sharing,
    skills,
    social,
    source_updates,
    staff,
    staff_products,
    training,
    travel_cases,
    uniform,
    user_context,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
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
    app.include_router(battle_rhythm.router)
    app.include_router(billets.router)
    app.include_router(career.router)
    app.include_router(context.router)
    app.include_router(custom_watch_feeds.router)
    app.include_router(demo.router)
    app.include_router(connectors.router)
    app.include_router(documents.router)
    app.include_router(handoffs.router)
    app.include_router(calendar.router)
    app.include_router(chief.router)
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
    app.include_router(section_memory.router)
    app.include_router(maradmins.router)
    app.include_router(message_watch.router)
    app.include_router(social.router)
    app.include_router(staff.router)
    app.include_router(staff_products.router)
    app.include_router(sharing.router)
    app.include_router(skills.router)
    app.include_router(source_updates.router)
    app.include_router(training.router)
    app.include_router(travel_cases.router)
    app.include_router(uniform.router)
    app.include_router(user_context.router)
    # Use absolute path so the dashboard serves correctly regardless of
    # the working directory the server is launched from (fixes #21 extension)
    _static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
    return app


app = create_app()
