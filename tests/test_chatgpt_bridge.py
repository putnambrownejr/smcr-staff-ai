import pytest

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter
from app.chatgpt_bridge.server_stub import ChatGptBridgeServerStub
from app.main import app


def test_chatgpt_bridge_catalog_contains_expected_tools() -> None:
    stub = ChatGptBridgeServerStub(adapter=ChatGptBridgeAdapter(app=app))

    catalog = stub.tool_catalog()

    tool_names = [tool.name for tool in catalog.tools]
    assert "chief_brief_demo" in tool_names
    assert "summarize_text_demo" in tool_names


@pytest.mark.anyio
async def test_chatgpt_bridge_adapter_calls_demo_routes() -> None:
    adapter = ChatGptBridgeAdapter(app=app)

    chief = await adapter.chief_brief_demo()
    summary = await adapter.summarize_text_demo(
        {"text": "DTS voucher due NLT 06/10/2026. Confirm muster timeline.", "focus": "drill prep"}
    )

    assert chief["user_key"] == "demo-smcr-officer"
    assert summary["summary_points"]
