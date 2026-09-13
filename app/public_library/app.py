from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from mcp.server.transport_security import TransportSecuritySettings

from app.public_library.catalog import PublicCatalog
from app.public_library.models import DRAFT_NOTICE, Category, LibraryItem, SearchResults
from app.public_library.server import create_mcp_server
from app.public_library.settings import PublicSettings

STATIC_DIR = Path(__file__).with_name("static")


def create_app(settings: PublicSettings | None = None, catalog: PublicCatalog | None = None) -> FastAPI:
    settings = settings or PublicSettings()
    catalog = catalog or PublicCatalog.load()
    mcp = create_mcp_server(catalog)
    mcp_app = mcp.streamable_http_app(
        json_response=True, stateless_http=True, max_request_body_size=16384,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=settings.allowed_hosts, allowed_origins=[settings.base_url],
        ),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        async with mcp.session_manager.run():
            yield

    application = FastAPI(
        title="SMCR Public Library", version="0.1.0", lifespan=lifespan,
        description="Public references and advisory drafts only. " + DRAFT_NOTICE,
        docs_url=None, redoc_url=None, openapi_url=None,
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Health probes need no configured host; all content routes do.
        if request.url.path != "/health" and request.headers.get("host") not in settings.allowed_hosts:
            return PlainTextResponse("Unrecognized host.", status_code=421)
        origin = request.headers.get("origin")
        if origin is not None and origin != settings.base_url:
            return PlainTextResponse("Unrecognized origin.", status_code=403)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "smcr-public-library", "access": "public-read-only"}

    @application.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/api/catalog", response_model=SearchResults)
    def search(
        q: str = Query(default="", max_length=200), category: Category | None = None,
        limit: int = Query(default=12, ge=1, le=30), offset: int = Query(default=0, ge=0, le=10000),
    ) -> SearchResults:
        return catalog.search(q, category, limit, offset)

    @application.get("/api/items/{item_id}", response_model=LibraryItem)
    def get_item(item_id: str) -> LibraryItem:
        try:
            return catalog.get(item_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @application.get("/api/connection")
    def connection() -> dict[str, str]:
        return {"url": settings.base_url + "/mcp", "transport": "streamable-http", "authentication": "none"}

    application.mount("/assets", StaticFiles(directory=STATIC_DIR), name="public-assets")
    # Mount last so /mcp is served without a redirect; lifespan is owned above.
    application.mount("/", mcp_app)
    return application


app = create_app()
