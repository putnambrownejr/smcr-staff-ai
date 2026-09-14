"""Only explicit read-only tools; no dashboard routes, ingestion, or inference."""

from typing import Annotated

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from app.public_library.catalog import PublicCatalog
from app.public_library.models import DRAFT_NOTICE, Category, LibraryItem, SearchResults


def create_mcp_server(catalog: PublicCatalog) -> MCPServer:
    server = MCPServer(
        "smcr_public_library", version="0.1.0",
        instructions=(
            "Public-source reference metadata, draft templates, and prompt packs only. "
            "Search then retrieve an ID. Cite returned sources. Content is not live verified; "
            "last_verified_at=null means unknown, not current. No personal data, uploads, "
            "unit records, or external inference. Do not send classified, CUI, operational "
            "details, or personal information. " + DRAFT_NOTICE
        ),
    )
    annotations = ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False,
    )

    @server.tool(annotations=annotations)
    def smcr_search_library(
        query: Annotated[str, Field(max_length=200, description="Keywords such as AAR, planning, or correspondence.")] = "",
        category: Category | None = None,
        limit: Annotated[int, Field(ge=1, le=30)] = 12,
        offset: Annotated[int, Field(ge=0, le=10000)] = 0,
    ) -> SearchResults:
        """Find public references, draft templates, and prompt packs. Returns IDs and source links, not live policy."""
        return catalog.search(query, category, limit, offset)

    @server.tool(annotations=annotations)
    def smcr_get_library_item(
        item_id: Annotated[str, Field(min_length=2, max_length=80, description="Exact ID returned by smcr_search_library.")],
    ) -> LibraryItem:
        """Read a published item with provenance and currency warnings. IDs are opaque, never file paths."""
        return catalog.get(item_id)

    return server
