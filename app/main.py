from fastapi import FastAPI

from app.api.routes import (
    agents,
    analysis,
    billets,
    calendar,
    career,
    chief,
    connectors,
    context,
    demo,
    documents,
    handoffs,
    health,
    opportunities,
    org,
    personal_documents,
    reading,
    social,
    staff,
    staff_products,
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
    app.include_router(analysis.router)
    app.include_router(agents.router)
    app.include_router(billets.router)
    app.include_router(career.router)
    app.include_router(context.router)
    app.include_router(demo.router)
    app.include_router(connectors.router)
    app.include_router(documents.router)
    app.include_router(handoffs.router)
    app.include_router(calendar.router)
    app.include_router(chief.router)
    app.include_router(org.router)
    app.include_router(opportunities.router)
    app.include_router(personal_documents.router)
    app.include_router(reading.router)
    app.include_router(social.router)
    app.include_router(staff.router)
    app.include_router(staff_products.router)
    return app


app = create_app()
