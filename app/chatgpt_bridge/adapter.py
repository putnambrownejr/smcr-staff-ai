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
        self._discovered_base_url: str | None = None

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

    async def build_frago_to_conop(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/planning/frago-to-conop", json=payload)

    async def draft_staff_product(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/staff-products/draft", json=payload)

    async def build_training_case_study(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/training/case-study", json=payload)

    async def build_tdg(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/training/tdg", json=payload)

    async def build_staff_update_cycle(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/staff/update-cycle", json=payload)

    async def run_opt_facilitator(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.run_staff_agent(agent_id="opt-facilitator", payload=payload)

    async def run_red_team_assumptions_challenge(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.run_staff_agent(agent_id="red-team-assumptions-challenge", payload=payload)

    async def run_assessment_learning_advisor(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.run_staff_agent(agent_id="assessment-learning-advisor", payload=payload)

    async def list_agents(self) -> dict[str, Any]:
        return {"agents": await self._request_list("GET", "/agents")}

    async def run_staff_agent(self, *, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", f"/agents/{agent_id}/run", json=payload)

    async def build_chief_brief(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/chief/brief", json=payload, include_local_api_key=True)

    async def build_next_drill_readiness(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/chief/brief", json=payload, include_local_api_key=True)

    async def get_career_watch(self, *, user_key: str) -> dict[str, object]:
        return await self._request_dict("GET", f"/career/watch/{user_key}", include_local_api_key=True)

    async def get_admin_readiness(self, *, user_key: str) -> dict[str, object]:
        return await self._request_dict("GET", f"/admin/readiness/{user_key}", include_local_api_key=True)

    async def build_admin_workflow(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict("POST", "/admin/workflow", json=payload, include_local_api_key=True)

    async def build_handoff_reminder_plans(
        self, *, user_key: str, payload: dict[str, object] | None = None
    ) -> dict[str, object]:
        return await self._request_dict(
            "POST",
            f"/calendar/handoffs/{user_key}/reminder-plans",
            json=payload or {},
            include_local_api_key=True,
        )

    async def build_external_ai_packet(self, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict(
            "POST",
            "/sharing/external-ai-packet",
            json=payload,
            include_local_api_key=True,
        )

    async def get_active_user_context(self, *, user_key: str) -> dict[str, object]:
        return await self._request_dict("GET", f"/user-context/{user_key}", include_local_api_key=True)

    async def set_active_user_context(self, *, user_key: str, payload: dict[str, object]) -> dict[str, object]:
        return await self._request_dict(
            "PUT",
            f"/user-context/{user_key}",
            json=payload,
            include_local_api_key=True,
        )

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

        if self.app is None and self.client_factory is None:
            await self._ensure_base_url()

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

    async def _ensure_base_url(self) -> None:
        if self._discovered_base_url is not None:
            self.base_url = self._discovered_base_url
            return

        if self.base_url != "http://127.0.0.1:8000":
            self._discovered_base_url = self.base_url
            return

        discovered = await self._discover_backend_url()
        self._discovered_base_url = discovered
        self.base_url = discovered

    async def _discover_backend_url(self) -> str:
        candidate_ports = [8000, 8001, 8005, 8002, 8003, 8004, 8006, 8007, 8008, 8009, 8010]
        for port in candidate_ports:
            candidate = f"http://127.0.0.1:{port}"
            try:
                async with httpx.AsyncClient(base_url=candidate, timeout=2.0) as client:
                    response = await client.get("/openapi.json")
                    if response.status_code != 200:
                        continue
                    payload = response.json()
                    paths = payload.get("paths", {})
                    if "/planning/staff-package" not in paths or "/agents" not in paths:
                        continue

                    route_probe = await client.post(
                        "/planning/staff-package",
                        json={
                            "title": "probe",
                            "mission_or_training_goal": "probe",
                            "training_only": True,
                        },
                    )
                    if route_probe.status_code != 404:
                        return candidate
            except Exception:
                continue
        return self.base_url
