import asyncio

import httpx
import pytest

from app.public_library.models import DRAFT_NOTICE


def test_http_catalog_and_no_private_routes(public_url: str) -> None:
    with httpx.Client(base_url=public_url) as client:
        assert client.get("/health").json()["access"] == "public-read-only"
        result = client.get("/api/catalog", params={"q": "AAR", "category": "template"})
        assert result.status_code == 200
        assert result.json()["items"][0]["id"] == "sys-aar"
        item = client.get("/api/items/sys-aar").json()
        assert DRAFT_NOTICE in item["content"]
        assert client.get("/api/connection").json()["url"] == public_url + "/mcp"
        assert client.get("/api/items/not-a-real-item").status_code == 404
        assert client.get("/api/catalog", params={"limit": 1000}).status_code == 422
        for path in ("/dashboard", "/user-profiles", "/sharing/external-ai-packet", "/.env", "/assets/../catalog.json"):
            assert client.get(path).status_code == 404
        for path in ("/dashboard/shutdown", "/git/pull", "/user-docs/upload", "/demo/workspace/seed"):
            assert client.post(path).status_code == 404
        assert client.post("/api/items/sys-aar", json={"content": "overwrite"}).status_code in (404, 405)
        assert client.get("/api/items/sys-aar").json()["content"] == item["content"]


def test_origin_host_headers_and_content_security(public_url: str) -> None:
    with httpx.Client(base_url=public_url) as client:
        assert client.get("/api/catalog", headers={"Host": "attacker.invalid"}).status_code == 421
        assert client.get("/api/catalog", headers={"Origin": "https://attacker.invalid"}).status_code == 403
        response = client.get("/")
        assert response.status_code == 200
        assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "no-referrer"


def test_mcp_legacy_protocol_initialize_list_and_call(public_url: str) -> None:
    headers = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"}
    with httpx.Client(base_url=public_url, headers=headers) as client:
        initialized = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "compatibility-test", "version": "1"}},
        })
        assert initialized.status_code == 200
        assert initialized.json()["result"]["protocolVersion"] == "2025-11-25"
        listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}).json()
        assert {tool["name"] for tool in listed["result"]["tools"]} == {"smcr_search_library", "smcr_get_library_item"}
        called = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "smcr_get_library_item", "arguments": {"item_id": "sys-aar"}},
        }).json()
        assert called["result"]["structuredContent"]["id"] == "sys-aar"
        assert called["result"]["isError"] is False
        assert client.post("/mcp", content="x" * 17000).status_code == 413


def test_official_mcp_client_over_http(public_url: str) -> None:
    pytest.importorskip("mcp")
    from mcp import Client

    async def exercise() -> None:
        async with Client(public_url + "/mcp", read_timeout_seconds=10) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {"smcr_search_library", "smcr_get_library_item"}
            for tool in tools.tools:
                assert tool.annotations is not None
                assert tool.annotations.read_only_hint is True
                assert tool.annotations.open_world_hint is False
                assert tool.output_schema
            results = await client.call_tool("smcr_search_library", {"query": "AAR", "category": "template"})
            assert not results.is_error
            assert results.structured_content is not None
            item_id = results.structured_content["items"][0]["id"]
            item = await client.call_tool("smcr_get_library_item", {"item_id": item_id})
            assert item.structured_content is not None
            assert item.structured_content["last_verified_at"] is None
            assert item.structured_content["notice"] == DRAFT_NOTICE
            bad = await client.call_tool("smcr_search_library", {"limit": 9999})
            assert bad.is_error
            traversal = await client.call_tool("smcr_get_library_item", {"item_id": "../../.env"})
            assert traversal.is_error

    asyncio.run(exercise())
