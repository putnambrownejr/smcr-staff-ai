from __future__ import annotations

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter
from app.chatgpt_bridge.schemas import BridgeCatalog


class ChatGptBridgeServerStub:
    """
    Minimal bridge surface for a future MCP/Apps server.

    This module intentionally stays dependency-light. It defines the tool catalog and
    handler methods we would later register with a real MCP server runtime.
    """

    def __init__(self, adapter: ChatGptBridgeAdapter | None = None) -> None:
        self.adapter = adapter or ChatGptBridgeAdapter()

    def tool_catalog(self) -> BridgeCatalog:
        return self.adapter.catalog()

    async def chief_brief_demo(self) -> dict[str, object]:
        return await self.adapter.chief_brief_demo()

    async def career_watch_demo(self) -> dict[str, object]:
        return await self.adapter.career_watch_demo()

    async def summarize_text_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.adapter.summarize_text_demo(payload)

    async def draft_staff_product_demo(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.adapter.draft_staff_product_demo(payload)

    async def run_staff_agent_demo(self, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return await self.adapter.run_staff_agent_demo(agent_id=agent_id, payload=payload)
