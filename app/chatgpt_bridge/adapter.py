from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx
from fastapi import FastAPI

from app.chatgpt_bridge.catalog import build_bridge_catalog
from app.chatgpt_bridge.schemas import BridgeCatalog


class ChatGptBridgeAdapter:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8000",
        app: FastAPI | None = None,
        client_factory: Callable[[], Awaitable[httpx.AsyncClient]] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.app = app
        self.client_factory = client_factory

    def catalog(self) -> BridgeCatalog:
        return build_bridge_catalog()

    async def chief_brief_demo(self) -> dict[str, object]:
        return await self._request("GET", "/demo/chief/brief")

    async def career_watch_demo(self) -> dict[str, object]:
        return await self._request("GET", "/demo/career/watch")

    async def summarize_text_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request("POST", "/demo/analysis/summarize", json=payload)

    async def draft_staff_product_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request("POST", "/demo/staff-products/draft", json=payload)

    async def run_staff_agent_demo(self, *, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request("POST", f"/demo/agents/{agent_id}/run", json=payload)

    async def _request(self, method: str, path: str, json: dict[str, object] | None = None) -> dict[str, object]:
        if self.client_factory is not None:
            client = await self.client_factory()
            try:
                response = await client.request(method, path, json=json)
                response.raise_for_status()
                return dict(response.json())
            finally:
                await client.aclose()

        if self.app is not None:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
                response = await client.request(method, path, json=json)
                response.raise_for_status()
                return dict(response.json())

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.request(method, path, json=json)
            response.raise_for_status()
            return dict(response.json())
