from typing import cast

import pytest

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter
from app.main import create_app


@pytest.mark.anyio
async def test_build_staff_package_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_staff_package(
        {
            "title": "Adapter planning test",
            "event_type": "field_training",
            "mission_or_training_goal": "Improve drill-weekend field execution.",
            "product_types": ["warno", "aar"],
            "training_only": True,
        }
    )

    assert "Adapter planning test" in cast(str, result["title"])
    assert "recommended_course_of_action" in result
    assert "xo_vet" in result


@pytest.mark.anyio
async def test_draft_staff_product_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.draft_staff_product(
        {
            "product_type": "warno",
            "topic": "Training-only event",
            "training_or_fictional": True,
        }
    )

    assert result["product_type"] == "warno"
    assert "sections" in result


@pytest.mark.anyio
async def test_list_agents_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.list_agents()

    assert "agents" in result
    assert any(agent["id"] == "s3-opso" for agent in result["agents"])
