from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

import httpx
from fastapi import FastAPI

from app.chatgpt_bridge.catalog import build_bridge_catalog
from app.chatgpt_bridge.schemas import BridgeCatalog


class ChatGptBridgeAdapter:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8000",
        local_api_key: str | None = None,
        app: FastAPI | None = None,
        client_factory: Callable[[], Awaitable[httpx.AsyncClient]] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.local_api_key = local_api_key
        self.app = app
        self.client_factory = client_factory

    def catalog(self) -> BridgeCatalog:
        return build_bridge_catalog()

    async def chief_brief_demo(self) -> dict[str, object]:
        return await self._request_dict("GET", "/demo/chief/brief")

    async def career_watch_demo(self) -> dict[str, object]:
        return await self._request_dict("GET", "/demo/career/watch")

    async def summarize_text_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/demo/analysis/summarize", json=payload)

    async def draft_staff_product_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/demo/staff-products/draft", json=payload)

    async def run_staff_agent_demo(self, *, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", f"/demo/agents/{agent_id}/run", json=payload)

    async def build_staff_package(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/planning/staff-package", json=payload)

    async def draft_staff_product(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/staff-products/draft", json=payload)

    async def list_agents(self) -> dict[str, Any]:
        return {"agents": await self._request_list("GET", "/agents")}

    async def run_staff_agent(self, *, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", f"/agents/{agent_id}/run", json=payload)

    async def build_chief_brief(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/chief/brief", json=payload, include_local_api_key=True)

    async def get_career_watch(self, *, user_key: str) -> dict[str, object]:
        return await self._request_dict("GET", f"/career/watch/{user_key}", include_local_api_key=True)

    async def get_admin_readiness(self, *, user_key: str) -> dict[str, object]:
        return await self._request_dict("GET", f"/admin/readiness/{user_key}", include_local_api_key=True)

    async def build_admin_workflow(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/admin/workflow", json=payload, include_local_api_key=True)

    async def _request_dict(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
        *,
        include_local_api_key: bool = False,
    ) -> dict[str, object]:
        return cast(
            dict[str, object],
            await self._request(method, path, json=json, include_local_api_key=include_local_api_key),
        )

    async def _request_list(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
        *,
        include_local_api_key: bool = False,
    ) -> list[dict[str, object]]:
        return cast(
            list[dict[str, object]],
            await self._request(method, path, json=json, include_local_api_key=include_local_api_key),
        )

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, object] | None = None,
        *,
        include_local_api_key: bool = False,
    ) -> Any:
        headers: dict[str, str] = {}
        if include_local_api_key and self.local_api_key:
            headers["X-Local-API-Key"] = self.local_api_key

        if self.client_factory is not None:
            client = await self.client_factory()
            try:
                response = await client.request(method, path, json=json, headers=headers)
                response.raise_for_status()
                return response.json()
            finally:
                await client.aclose()

        if self.app is not None:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
                response = await client.request(method, path, json=json, headers=headers)
                response.raise_for_status()
                return response.json()

        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.request(method, path, json=json, headers=headers)
            response.raise_for_status()
            return response.json()
